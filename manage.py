#!/usr/bin/env python
import os
import sys
from Fingerprints_django.settings import environment

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fingerprints_django.settings")

    from django.core.management import execute_from_command_line

    if "test" in sys.argv and environment == 'prod':
        sys.exit("Don't run tests on prod server - cache is shared!")

    execute_from_command_line(sys.argv)
