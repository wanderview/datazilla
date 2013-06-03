from optparse import make_option
from random import randint

from base import ProjectBatchCommand
from datazilla.controller.admin.email_send import email_send
from datazilla.util.bunch import Bunch
from datazilla.util.db import get_database_connection
from datazilla.util.debug import D
from datazilla.model.utils import datazilla


class Command(ProjectBatchCommand):

    LOCK_FILE = "run_metrics"+str(randint(100000000, 999999999))

    help = "Run alert methods."

    option_list = ProjectBatchCommand.option_list + (
        make_option('--debug',
                    action='store_true',
                    dest='debug',
                    default=None,
                    help=('Send stuff to stdout')
        ),
        )


    def handle_project(self, project, **options):

        try:
            D.println("Running email for project ${project}", {"project":project})

            email_send(Bunch({
                "db":get_database_connection(project, "perftest"),
                "debug":options.get('debug') or datazilla.settings.DEBUG,
            }))
        except Exception, e:
            D.warning("Failure to run alerts", cause=e)

