"""
Main file for invoke tasks. We auto-import all modules here, so that
one can simply add tasks by adding files.
"""

import os

from invoke import Collection, Task
import warnings


warnings.warn(
    "Invoke scripts are deprecated and will be removed in ImageIO v3. They"
    " have been superseeded by CI scripts and there is currently no plan to"
    " keep invoke. If you want to keep them, please open a new issue so"
    " that we can discuss.",
    DeprecationWarning,
)

# Get root directory of the package
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)

# Init collection; invoke picks this up as the main "list of tasks"
ns = Collection()

# Automatically collect tasks from submodules
for fname in os.listdir(THIS_DIR):
    # Does this look like a module that we want?
    if fname.startswith("_") or not fname.endswith(".py"):
        continue
    modname = fname[:-3]
    # Import it
    m = __import__(modname, level=1, fromlist=[], globals=globals())
    # Collect all tasks and collections
    collections, tasks = {}, {}
    for name in dir(m):
        ob = getattr(m, name)
        if isinstance(ob, Task):
            tasks[name] = ob
        elif isinstance(ob, Collection):
            collections[name] = ob
    # Add collections
    for name, ob in collections.items():
        ns.add_collection(ob, name)
    # Add tasks that are not already in a collection
    for name, ob in tasks.items():
        add_task = True
        for c in collections.values():
            if ob in c.tasks.values():
                add_task = False
        if add_task:
            ns.add_task(ob, name)
