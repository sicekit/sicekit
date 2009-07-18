__version__ = '$Id: wikipediatools.py 6630 2009-04-19 08:47:15Z cosoleto $'
import os, sys

def create_user_config_file():
    import generate_user_files
    generate_user_files.create_user_config()

def get_base_dir():
    """Return the directory in which user-specific information is stored.

    This is determined in the following order -
    1.  If the script was called with a -dir: argument, use the directory
        provided in this argument
    2.  If the user has a PYWIKIBOT_DIR environment variable, use the value
        of it
    3.  If the script was started from a directory that contains a
        user-config.py file, use this directory as the base
    4.  If all else fails, use the directory from which this module was
        loaded.
    5.  If the user-config.py file is not found, another will be created
        in the current directory, following in the footsteps of project,
        language and bot username.

    """
    for arg in sys.argv[1:]:
        if arg.startswith("-dir:"):
            base_dir = arg[5:]
            sys.argv.remove(arg)
            break
    else:
        if "PYWIKIBOT_DIR" in os.environ:
            base_dir = os.environ["PYWIKIBOT_DIR"]
        else:
            if os.path.exists('user-config.py'):
                base_dir = '.'
            else:
                try:
                    base_dir = os.path.split(
                                sys.modules['wikipediatools'].__file__)[0]
                except KeyError:
                    print sys.modules
                    base_dir = '.'
    if not os.path.isabs(base_dir):
        base_dir = os.path.normpath(os.path.join(os.getcwd(), base_dir))
    # make sure this path is valid and that it contains user-config file
    if not os.path.isdir(base_dir):
        raise RuntimeError("Directory '%s' does not exist." % base_dir)
    if not os.path.exists(os.path.join(base_dir, "user-config.py")):
        print("No user-config.py found in directory '%s'" % base_dir)
        print("Creating...\n")
        create_user_config_file()
    return base_dir
