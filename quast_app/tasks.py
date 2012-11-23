from shutil import copytree
import shutil
import sys
import os
import traceback
from celery.task import task
from django.conf import settings
from django.core.mail import send_mail


@task()
def start_quast((args, quast_session)):
    link = os.path.join(settings.REPORT_LINK_BASE, quast_session.report_id)

    from_email = 'notification@quast.bioinf.spbau.ru'
    def send_result_mail(email, add_to_end='', fail=False):
        if email is None or email == '':
            return

        if fail:
            subject = 'Quast failed'
        else:
            subject = 'Quast report'

        if quast_session.caption:
            subject += ' (%s)' % quast_session.caption
        elif quast_session.dataset:
            subject += ' (data set: %s)' % quast_session.dataset.name

        send_mail(
            subject = subject,
            message =
                (quast_session.caption + '\n\n' if quast_session.caption else '') +
                'http://quast.bioinf.spbau.ru' + link +
                ('\n\nData set: ' + quast_session.dataset.name if quast_session.dataset else '') +
                ('\n\nComment: ' + quast_session.comment if quast_session.comment else '') +
                add_to_end,
            from_email = from_email,
            recipient_list = [email],
            fail_silently = True
        )

    my_email = 'vladsaveliev@me.com'
    if quast_session.user_session.email:
        user_email = quast_session.user_session.email
    else:
        user_email = None

    try:
        if not settings.QUAST_DIRPATH in sys.path:
            sys.path.insert(1, settings.QUAST_DIRPATH)
        import quast

        quast.qconfig.html_report = False
        quast.qconfig.draw_plots = False

        result = quast.main(args[1:])

        add_to_end = '\n\nUser email: ' + user_email + \
                     '\n\nSession key: ' + quast_session.user_session.session_key + \
                     '\n\nArgs: ' + str(args)

        send_result_mail(my_email, add_to_end=add_to_end)
        send_result_mail(user_email)

    except Exception as e:
        trace_back = traceback.format_exc()
        add_to_end = '\n\nUser email: ' + str(user_email) + \
                     '\n\nSession key: ' + quast_session.user_session.session_key + \
                     '\n\nArgs: ' + str(args) + \
                     '\n\nException: ' + str(e) + \
                     '\n\nTraceback: ' + str(trace_back)

        send_result_mail(my_email, add_to_end, fail=True)
        send_result_mail(user_email, fail=True)
        raise e

    reload(quast)
    return result

#   out = ''
#   err = ''
#   try:
#       proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#       while True:
#           line = proc.stderr.readline()
#           if line != '':
#               out = out + 'Quast err ' + line + '\n'
#           else:
#               break
#       proc.wait()
#
#   except Exception as e:
#       raise Exception(out + err + '\n' + e.strerror)