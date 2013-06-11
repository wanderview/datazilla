# Source Code is subject to the terms of the Mozilla Public License
# version 2.0 (the "License"). You can obtain a copy of the License at
# http://mozilla.org/MPL/2.0/.
from datetime import datetime

from datazilla.util.debug import D


#if there are emails, then send them
from datazilla.util.map import Map

def email_send(**env):
    env=Map(**env)
    assert env.db is not None               #EXPECTING db WITH EMAIL SCHEMA
    assert env.emailer is not None          #EXPECTING SMTP CONNECTION INFO

    db = env.db
    emailer=env.emailer
    db.debug=env.debug



    ##VERIFY self SHOULD BE THE ONE PERFORMING OPS (TO PREVENT MULTIPLE INSTANCES NEEDLESSLY RUNNING)
    db.begin()

    try:

        ## EXIT EARLY IF THERE ARE NO EMAILS TO SEND
        has_mail = db.query("SELECT max(new_mail) new_mail FROM email_notify")
        if has_mail[0]["new_mail"]==0:
            D.println("No emails to send")
            return

        ## GET LIST OF MAILS TO SEND
        emails = db.query("""
            SELECT
                c.id,
                group_concat(d.deliver_to SEPARATOR ',') `to`,
                c.subject,
                c.body
            FROM
                email_content c
            LEFT JOIN
                email_delivery d ON d.content=c.id
            WHERE
                c.date_sent IS NULL
            GROUP BY
                c.id

            """)

        ## SEND MAILS
        not_done=0   ##SET TO ONE IF THERE ARE MAIL FAILURES, AND THERE ARE MAILS STILL LEFT TO SEND
        num_done=0
        for email in emails:
            try:
                emailer.send_email(
                    to_addrs=email.to.split(','),
                    subject=email.subject,
                    html_data=email.body
                )

                db.execute("UPDATE email_content SET date_sent=${now} WHERE id=${id}",{"id":email.id, "now":datetime.utcnow()})
                num_done+=len(email.to.split(','))
            except Exception, e:
                D.warning("Problem sending email", e)
                not_done=1

        db.execute("UPDATE email_notify SET new_mail=${not_done}", {"not_done":not_done})

        D.println(str(num_done)+" emails have been sent")
        db.commit()
    except Exception, e:
        db.rollback()
        D.error("Could not send emails", e)


