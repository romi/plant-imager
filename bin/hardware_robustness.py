#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from shutil import rmtree

import toml

from plantdb import FSDB
from plantdb.fsdb import LOCK_FILE_NAME
from plantdb.fsdb import MARKER_FILE_NAME
from romitask.log import configure_logger

dirname, filename = os.path.split(os.path.abspath(__file__))

URL = "https://docs.romi-project.eu/plant_imager/developer/pipeline_repeatability/"
DATETIME_FMT = "%Y.%m.%d_%H.%M"

DESC = """Robustness evaluation of the Plant Imager hardware.

Can be used to acquire the scan dataset to compare.
Then it simply create an animation as a sequence of images.
If you can see differences between images, there is some variability in the acquisition hardware!
"""


def parsing():
    parser = argparse.ArgumentParser(description=DESC,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=f"Detailed explanations here: {URL}")

    parser.add_argument("db_location", type=str,
                        help="Location of the DB containing the scans to use for repeatability evaluation.")

    task = parser.add_argument_group('Task options')
    task.add_argument("-t", "--task", default='Scan', type=str, choices={"Scan", "CalibrationScan"},
                      help="Name of the task to performs to evaluate hardware robustness")
    task.add_argument("-c", "--config", type=str,
                      help="TOML configuration file to performs the scan.")
    task.add_argument("-n", "--n_repeats", type=int, default=5,
                      help="Number of Scan repetition to performs.")

    # -- Evaluation options:
    eval = parser.add_argument_group('Evaluation options')
    eval.add_argument("--no_scan", action="store_true", default=False,
                      help="Use this to avoid acquisition of scans dataset.")
    eval.add_argument("--prefix", default="", type=str,
                      help="Use this to define a prefix name to use for the scans to acquire OR to select a group of scans to evaluate, based on a common prefix in their names.")

    # -- GIF options:
    gif = parser.add_argument_group('GIF options')
    gif.add_argument("--image_id", default='00000_rgb', type=str,
                     help="Name of the image to use to create the GIF. Defaults to `00000_rgb`.")
    gif.add_argument("--delay", default=100, type=int,
                     help="Delay between images in the created GIF, in milliseconds. Defaults to `100`.")

    parser.add_argument('--log-level', dest='log_level', type=str, default='INFO',
                        choices=list(logging._nameToLevel.keys()),
                        help="Set message logging level. Defaults to `INFO`.")

    return parser


def _check_markers(path):
    # - Make sure the `romidb` marker file exists:
    marker_file = path / MARKER_FILE_NAME
    try:
        marker_file.touch()
    except:
        pass
    # - Make sure the `lock` file do NOT exist:
    lock_file = path / LOCK_FILE_NAME
    try:
        lock_file.unlink()
        # lock_file.unlink(missing_ok=True)  # missing_ok only available since Python3.8
    except:
        pass
    return


def check_scan_configs(scans_list):
    """Check the scan configuration is the same as the reference.

    Parameters
    ----------
    scans_list : list of plantsb.FSDB.Scan
        List of ``Scan`` instances to compare.

    Returns
    -------
    bool
        ``True`` if the scan configurations are the same, else ``False``.

    Examples
    --------
    >>> import os, toml
    >>> from pathlib import Path
    >>> from plantdb.fsdb import FSDB
    >>> db = FSDB(os.environ.get('ROMI_DB', '/home/aurele/Downloads/20221010_Jo/Scans/'))
    >>> db.connect()  # print the list of scan dataset names
    >>> check_scan_configs(db.get_scans())
    >>> db.disconnect()

    """
    same_cfg = True
    ref_scan_cfg = {}

    for scan in scans_list:
        bak_cfg_file = Path(scan.path()) / "scan.toml"
        if not bak_cfg_file.is_file():
            logger.warning(f"Could not load backup `scan.toml` for scan id '{scan.id}'!")
            continue
        cfg = toml.load(str(bak_cfg_file))
        scan_cfg = cfg['ScanPath']
        if ref_scan_cfg == {}:
            ref_scan_cfg = scan_cfg.deepcopy()
        else:
            same_type = compare_scan_type(ref_scan_cfg, scan_cfg)
            same_params = compare_scan_params(ref_scan_cfg, scan_cfg)
    return

def compare_scan_type(ref_scan_cfg, scan_cfg):
    # - Check the type of 'ScanPath' is the same:
    try:
        assert ref_scan_cfg['class_name'] == scan_cfg['class_name']
    except AssertionError:
        return False
    else:
        return True


def compare_scan_params(ref_scan_cfg, scan_cfg):
    # - Check the parameters of 'ScanPath' are the same:
    diff_keys = list(dict(set(ref_scan_cfg['kwargs'].items()) ^ set(scan_cfg['kwargs'].items())).keys())
    try:
        assert len(diff_keys) == 0
    except AssertionError:
        diff1, diff2 = _get_diff_between_dict(ref_scan_cfg['kwargs'], scan_cfg['kwargs'])
        logger.info(f"From reference scan: {diff1}")
        logger.info(f"From compared scan: {diff2}")
        return False
    else:
        return True


def romi_run_task(scan_path, task_name, cfg_file):
    """Run configured pipeline for given task on a scan.

    Parameters
    ----------
    scan_path : pathlib.Path or str
       Path to the scan dataset directory.
    task_name : str
        Name of the ROMI task to run.
    cfg_file : str
        Path to the configuration file to use to run the pipeline (``romi_run_task``).

    """
    logger.info(f"Executing task '{task_name}' on scan dataset '{str(scan_path)}'.")
    cmd = ["romi_run_task", task_name, str(scan_path), "--config", cfg_file, "--local-scheduler"]
    subprocess.run(cmd, check=True)
    return


def _get_diff_between_dict(d1, d2):
    """Return the entries that are different between two dictionaries."""
    diff_keys = list(dict(set(d1.items()) ^ set(d2.items())).keys())
    diff1 = {k: d1.get(k, None) for k in diff_keys}
    diff2 = {k: d2.get(k, None) for k in diff_keys}
    return diff1, diff2


def make_animation(db_location, imgs, img_fname, delay):
    """Make the animation as a sequence of images taken at the same position.

    Parameters
    ----------
    db_location : pathlib.Path or str
       Path to the database directory.
    imgs : dict
        ``Scan.id`` indexed dict of selected `img_fname`
    img_fname : str
        Name (without extension) of the image (from the .
    delay : int
        The delay between successive frames

    Returns
    -------

    """
    # Initialize a temporary directory use to store scan dataset before cleaning and running previous tasks to task to analyse:
    tmp_dir = tempfile.mkdtemp()
    # - Get the path of the temporary ROMI database
    tmp_path = Path(tmp_dir)
    logger.debug(f"Create a temporary directory '{tmp_path}' to modify the images prior to animation...")

    # Copy the image to temporary directory:
    annotated_imgs = {}
    for n, (scan_id, img) in enumerate(imgs.items()):
        img_fname = str(Path(img).stem) + f'_{n}' + '.jpg'
        annotated_imgs[scan_id] = f"{tmp_path}/{img_fname}"
        subprocess.run(["cp", img, annotated_imgs[scan_id]])

    # Add the scan name to image
    for scan_id, img in annotated_imgs.items():
        cmd = ['mogrify', '-font', 'Liberation-Sans', '-fill', 'white', '-undercolor', "black", '-pointsize', '26',
               '-gravity', 'NorthEast', '-annotate', '+10+10', f"'{scan_id}/{img_fname}'", img]
        subprocess.run(cmd)

    gif_fname = str(db_location / Path(str(Path(img_fname).stem) + '.gif'))
    cmd = ["convert", "-delay", f"{delay}"] + sorted(map(str, annotated_imgs.values())) + [gif_fname]
    subprocess.run(cmd, check=True)
    rmtree(tmp_path)
    logger.info(f"Generated the GIF animation: '{gif_fname}'.")


def main(args):
    # - Get the path to DB (directory) used to save the repeated scans:
    db_location = Path(args.db_location).expanduser()

    # - Initialize the logger
    global logger
    logger = configure_logger(filename, db_location, args.log_level)
    logger.info(f"Path to the 'repeated scans' database is: '{db_location}'")

    # Check the ROMI marker files and connect to the local database:
    _check_markers(db_location)
    db = FSDB(str(db_location))
    db.connect()

    if args.no_scan:
        # -- CASE where performing images acquisition is NOT required:
        logger.info(f"Using previously acquired dataset!")
        # Get the Scan instances from DB:
        scans = db.get_scans()
        logger.info(f"Found {len(scans)} Scans in current database!")
        # Filter the Scan instances using the prefix, if any:
        if args.prefix != "":
            scans = [scan for scan in scans if scan.id.startswith(args.prefix)]
            logger.info(f"Selected {len(scans)} Scans with prefix '{args.prefix}'!")
        # TODO: Load backup configuration files to make sure we have repeated scans!
        # check_scan_configs(scans)
    else:
        # -- CASE where performing images acquisition is required:
        scan_names = []
        prefix = getattr(args, "prefix", "hw_repeat")
        for n in range(args.n_repeats):
            # Create a scan dataset name using prefix and DATETIME:
            now = datetime.now()
            now_str = now.strftime(DATETIME_FMT)
            scan_name = prefix + f"_{now_str}"
            # Get the path to the scan dataset to create:
            scan_path = db_location.joinpath(scan_name)
            # Performs the acquisition job:
            romi_run_task(scan_path, args.task, args.config)
            scan_names += [scan_name]
        # Search in DB for Scan instances using acquired scan dataset names:
        scans = db.get_scans()
        scans = [scan for scan in scans if scan.id in scan_names]

    # - Get selected `image_id` from 'images' Filesets from each Scan:
    imgs = {}  # Scan.id indexed dict of selected `image_id`
    for scan in scans:
        img_fs = scan.get_fileset('images')
        imgs[scan.id] = Path(img_fs.get_file(args.image_id).path()).absolute()

    make_animation(db_location, imgs, args.image_id, args.delay)
    return

if __name__ == '__main__':
    # - Parse the input arguments to variables:
    parser = parsing()
    args = parser.parse_args()
    main(args)
