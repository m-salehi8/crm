from .models import *


def contract_migration():
    for c in Contract.objects.all():
        if c.locked:
            c.manager_accept = 'تأیید'
        c.fund_accept = 'تأیید' if c.prefunded else 'عدم تأیید'
        c.convention_accept = 'تأیید' if c.controlled else 'عدم تأیید'
        c.committee_accept = 'تأیید' if c.committee_accepted else 'عدم تأیید'
        c.deputy_accept = 'تأیید' if c.accepted else 'عدم تأیید'
        c.head_accept = 'تأیید' if c.accepted else 'عدم تأیید'
        c.draft_accept = c.draft_accepted

        if c.published:
            c.send_to_contractor_date = jdatetime.datetime.today().date()
            c.receive_from_contractor_date = jdatetime.datetime.today().date()
            c.signature_date = jdatetime.datetime.today().date()
        c.save()
        print('contract', c.id, 'OK')
    # for p in Pay.objects.all():
    #     p.manager_accept = p.controlled
    #     p.convention_accept = p.controlled
    #     p.fund_accept = p.controlled
    #     p.clerk_accept = p.controlled
    #     p.deputy_accept = p.accepted
    #     p.head_accept = p.accepted
    #     p.finance_accept = p.accepted
    #     print('pay', p.id, 'OK')
