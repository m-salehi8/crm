import json
import operator
import jdatetime
from cn.serializers import *
from functools import reduce
from prj.models import Project
from rest_framework import status
from core.models import Notification
from django.http import FileResponse
from core.permissions import IsPmUser
from rest_framework.response import Response
from prj.serializers import SerActiveProjectList
from django.db.models import Q, Case, When, Value
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView, GenericAPIView, CreateAPIView, DestroyAPIView, get_object_or_404, RetrieveAPIView, RetrieveDestroyAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter


class AgreementList(ListAPIView):
    serializer_class = SerAgreement
    queryset = Agreement.objects.all()


class ContractList(GenericAPIView):
    def get(self, request):
        if not request.user.groups.filter(name='pm').exists():
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)

        if request.GET.get('need_action', 'همه') == 'منتظر اقدام':
            contract_list = request.user.todo_contract_list()
        elif request.user.groups.filter(name__in=['supervisor', 'contract-admin', 'contract-deputy-accept', 'contract-head-accept', 'contract-fund-accept', 'contract-finance-accept', 'contract-warranty-add', 'contract-warranty-select', 'contract-pay-pay', 'contract-pay-audit']).exists():
            contract_list = Contract.objects.all()
        elif request.user.groups.filter(name='contract-committee-accept').exists():
            contract_list = Contract.objects.filter(Q(need_committee=True) | Q(project__unit=request.user.post.unit))
        else:
            contract_list = Contract.objects.filter(project__unit=request.user.post.unit)

        from_date = request.GET.get('from_date', None)
        to_date = request.GET.get('to_date', None)
        agreement = int(request.GET.get('agreement', 0))
        department = int(request.GET.get('department', 0))
        _type = request.GET.get('type', 'همه')
        genre = request.GET.get('genre', 'همه')
        order = request.GET.get('order', 'تاریخ ثبت')
        q = request.GET.get('q', None)
        manager_accept = request.GET.get('manager_accept', 'همه')
        fund_accept = request.GET.get('fund_accept', 'همه')
        convention_accept = request.GET.get('convention_accept', 'همه')
        need_committee = request.GET.get('need_committee', 'همه')
        committee_accept = request.GET.get('committee_accept', 'همه')
        deputy_accept = request.GET.get('deputy_accept', 'همه')
        head_accept = request.GET.get('head_accept', 'همه')
        drafted = request.GET.get('drafted', 'همه')
        draft_accept = request.GET.get('draft_accept', 'همه')
        send_to_contractor_date = request.GET.get('send_to_contractor_date', 'همه')
        receive_from_contractor_date = request.GET.get('receive_from_contractor_date', 'همه')
        signature_date = request.GET.get('signature_date', 'همه')
        secretariat_date = request.GET.get('secretariat_date', 'همه')
        warranty_type = request.GET.get('warranty_type', 'همه')
        f_warranty = request.GET.get('f_warranty', 'همه')
        f_acquittance = request.GET.get('f_acquittance', 'همه')
        archived = request.GET.get('archived', 'همه')

        if from_date:
            contract_list = contract_list.filter(start_date__gte=f'{from_date[:7]}-01')
        if to_date:
            contract_list = contract_list.filter(finish_date__lte=f'{to_date[:7]}-{31 if int(to_date[8:]) < 6 else 30 if int(to_date[8:]) < 12 else 29}')
        if agreement:
            contract_list = contract_list.filter(agreement_id=None if agreement == -1 else agreement)
        if department:
            contract_list = contract_list.filter(Q(project__unit_id=department) | Q(project__unit__parent_id=department))
        if _type != 'همه':
            contract_list = contract_list.filter(type=_type)
        if genre != 'همه':
            contract_list = contract_list.filter(genre=genre)
        if q:
            q_list = q.split(' ')
            q_filter = reduce(operator.and_, (Q(title__contains=q_text) | Q(tags__icontains=q_text) | Q(contractor__contains=q_text) | Q(cn_note__contains=q_text) | Q(no__contains=q_text) for q_text in q_list))
            contract_list = contract_list.filter(q_filter)
        if manager_accept != 'همه':
            contract_list = contract_list.filter(manager_accept=manager_accept)
        if fund_accept != 'همه':
            contract_list = contract_list.filter(fund_accept=fund_accept)
        if convention_accept != 'همه':
            contract_list = contract_list.filter(convention_accept=convention_accept)
        if need_committee != 'همه':
            contract_list = contract_list.filter(need_committee=need_committee == 'بله')
        if committee_accept != 'همه':
            contract_list = contract_list.filter(committee_accept=committee_accept)
        if deputy_accept != 'همه':
            contract_list = contract_list.filter(deputy_accept=deputy_accept)
        if head_accept != 'همه':
            contract_list = contract_list.filter(head_accept=head_accept)
        if drafted != 'همه':
            contract_list = contract_list.filter(drafted=drafted == 'بله')
        if draft_accept != 'همه':
            contract_list = contract_list.filter(draft_accept=None if draft_accept == 'نامشخص' else draft_accept == 'بله')
        if send_to_contractor_date != 'همه':
            contract_list = contract_list.filter(send_to_contractor_date__isnull=send_to_contractor_date == 'خیر')
        if receive_from_contractor_date != 'همه':
            contract_list = contract_list.filter(receive_from_contractor_date__isnull=receive_from_contractor_date == 'خیر')
        if signature_date != 'همه':
            contract_list = contract_list.filter(signature_date__isnull=signature_date == 'خیر')
        if secretariat_date != 'همه':
            contract_list = contract_list.filter(secretariat_date__isnull=secretariat_date == 'خیر')
        if warranty_type != 'همه':
            contract_list = contract_list.filter(warranty_type=warranty_type)
        if f_warranty == 'دارد':
            contract_list = contract_list.exclude(f_warranty__in=['', None])
        elif f_warranty == 'ندارد':
            contract_list = contract_list.filter(f_warranty__in=['', None])
        if f_acquittance == 'دارد':
            contract_list = contract_list.exclude(f_acquittance__in=['', None])
        elif f_acquittance == 'ندارد':
            contract_list = contract_list.filter(f_acquittance__in=['', None])
        if archived != 'همه':
            contract_list = contract_list.filter(archived=archived == 'بایگانی')

        size = request.user.profile.page_size
        page = min(int(request.GET.get('page', 1)), contract_list.count() // size + 1)
        contract_list = contract_list.order_by('-create_time' if order == 'تاریخ ثبت' else '-start_date')
        data = {
            'count': contract_list.count(),
            'page': page,
            'size': size,
            'list': SerContractList(instance=contract_list[size*(page-1):size*page], many=True).data
        }
        return Response(data=data)


def contract_can(contract, user):
    return {
        'see': user.groups.filter(name__in=['supervisor', 'contract-admin', 'contract-deputy-accept', 'contract-head-accept', 'contract-fund-accept', 'contract-warranty-add', 'contract-warranty-select', 'contract-committee-accept']).exists() or (user.groups.filter(name='pm').exists() and (contract.project.unit == user.post.unit or contract.project.unit.parent == user.post.unit)),
        'edit': contract.locked is False and (user == contract.registrar or (user.is_head_of_unit and (contract.project.unit == user.post.unit or contract.project.unit.parent == user.post.unit))),
        'manager_accept': contract.locked and contract.manager_accept == 'نامشخص' and user.is_head_of_unit and (contract.project.unit == user.post.unit or contract.project.unit.parent == user.post.unit),
        'fund_accept': contract.manager_accept == 'تأیید' and contract.fund_accept == 'نامشخص' and user.groups.filter(name='contract-fund-accept').exists(),
        'convention_accept': contract.fund_accept == 'تأیید' and contract.convention_accept == 'نامشخص' and user.groups.filter(name='contract-admin').exists(),
        'committee_accept': contract.convention_accept == 'تأیید' and contract.need_committee and contract.committee_accept == 'نامشخص' and user.groups.filter(name='contract-committee-accept').exists(),
        'deputy_accept': contract.convention_accept == 'تأیید' and contract.need_committee is False and contract.deputy_accept == 'نامشخص' and user.groups.filter(name='contract-deputy-accept').exists(),
        'head_accept': contract.deputy_accept == 'تأیید' and contract.head_accept == 'نامشخص' and user.groups.filter(name='contract-head-accept').exists(),
        'draft': contract.head_accept == 'تأیید' and (not contract.need_committee or contract.committee_accept == 'تأیید') and contract.drafted is False and user.groups.filter(name='contract-admin').exists(),
        'draft_accept': contract.drafted and contract.draft_accept is None and user == contract.registrar,
        'send_to_contractor': bool(contract.draft_accept) and contract.send_to_contractor_date is None and user.groups.filter(name='contract-admin').exists(),
        'receive_from_contractor': bool(contract.send_to_contractor_date) and contract.receive_from_contractor_date is None and user.groups.filter(name='contract-admin').exists(),
        'signature': bool(contract.receive_from_contractor_date) and contract.signature_date is None and user.groups.filter(name='contract-admin').exists(),
        'secretariat': bool(contract.signature_date) and contract.secretariat_date is None and user.groups.filter(name='contract-admin').exists(),
        'warranty_type': bool(contract.secretariat_date) and contract.warranty_type is None and user.groups.filter(name='contract-warranty-select').exists(),
        'f_warranty': bool(contract.warranty_type) and user.groups.filter(name='contract-warranty-add').exists(),  # برای الصاق مفاصا هم از همین دسترسی استفاده خواهد شد
        'archive': ((contract.secretariat_date and contract.f_acquittance not in ['', None]) or contract.manager_accept == 'عدم تأیید' or contract.fund_accept == 'عدم تأیید' or contract.convention_accept == 'عدم تأیید' or contract.committee_accept == 'عدم تأیید' or contract.deputy_accept == 'عدم تأیید' or contract.head_accept == 'عدم تأیید') and contract.archived is False and user.groups.filter(name='contract-admin').exists(),
    }


def pay_can(pay, user):
    return {
        'see': user.groups.filter(name__in=['supervisor', 'contract-admin', 'contract-deputy-accept', 'contract-head-accept', 'contract-fund-accept', 'contract-warranty-add', 'contract-warranty-select', 'contract-pay-audit', 'contract-pay-pay']).exists() or (user.groups.filter(name='pm').exists() and (pay.step.contract.project.unit == user.post.unit or pay.step.contract.project.unit.parent == user.post.unit)),
        'edit': pay.locked is False and (pay.registrar == user or pay.step.contract.registrar == user or pay.step.contract.project.unit.manager == user),
        'remove': (pay.locked is False and pay.manager_accept == 'نامشخص') and (pay.step.contract.registrar == user or pay.step.contract.project.unit.manager == user),
        'manager_accept': pay.locked and pay.manager_accept == 'نامشخص' and pay.step.contract.project.unit.manager == user,
        'convention_accept': pay.manager_accept == 'تأیید' and pay.convention_accept == 'نامشخص' and user.groups.filter(name='contract-admin').exists(),
        'fund_accept': pay.convention_accept == 'تأیید' and pay.fund_accept == 'نامشخص' and user.groups.filter(name='contract-fund-accept').exists(),
        'clerk_accept': pay.fund_accept == 'تأیید' and pay.clerk_accept == 'نامشخص' and user.groups.filter(name='contract-warranty-add').exists(),
        'deputy_accept': pay.clerk_accept == 'تأیید' and pay.deputy_accept == 'نامشخص' and user.groups.filter(name='contract-deputy-accept').exists(),
        'head_accept': pay.deputy_accept == 'تأیید' and pay.head_accept == 'نامشخص' and pay.need_head and user.groups.filter(name='contract-head-accept').exists(),
        'finance_accept': ((pay.need_head and pay.head_accept == 'تأیید') or (not pay.need_head and pay.deputy_accept == 'تأیید')) and pay.finance_accept == 'نامشخص' and user.groups.filter(name='contract-finance-accept').exists(),
        'audit': pay.finance_accept == 'تأیید' and pay.audit == 'نامشخص' and user.groups.filter(name='contract-pay-audit').exists(),
        'pay': pay.audit == 'تأیید' and pay.paid is None and user.groups.filter(name='contract-pay-pay').exists(),
    }


class ContractDetail(GenericAPIView):
    def get(self, request, no):
        contract = get_object_or_404(Contract, no=no)
        can = contract_can(contract, request.user)
        if not can['see']:
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        data = SerContractDetail(instance=contract).data
        data['can'] = can
        request.user.notifications.filter(contract=contract).update(seen_time=jdatetime.datetime.now())
        return Response(data=data)


class NewContractProjectList(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SerActiveProjectList

    def get_queryset(self):
        return Project.objects.filter(Q(unit=self.request.user.post.unit) | Q(unit__parent=self.request.user.post.unit))


class AddContract(CreateAPIView):
    permission_classes = [IsPmUser]
    queryset = Contract.objects.all()
    serializer_class = SerContractList


class UpdateContract(GenericAPIView):
    permission_classes = [IsPmUser]

    def post(self, request):
        contract = get_object_or_404(Contract, id=request.data['id'])
        if not contract_can(contract, request.user)['edit']:
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        contract.agreement_id = request.data['agreement']
        contract.project_id = request.data['project']
        contract.type = request.data['type']
        contract.genre = request.data['genre']
        contract.contractor = request.data['contractor']
        contract.contractor_no = request.data['contractor_no']
        contract.title = request.data['title']
        contract.price = request.data['price']
        contract.start_date = request.data['start_date']
        contract.finish_date = request.data['finish_date']
        contract.has_value_added = request.data['has_value_added']
        contract.period = request.data['period']
        contract.note = request.data['note']
        contract.tags = request.data['tags']
        contract.save()
        data = SerContractDetail(instance=contract).data
        data['can'] = contract_can(contract, request.user)
        return Response(data={'contract': data, 'todo_contract': request.user.todo_contract})


class UpdateContractAppendices(GenericAPIView):
    permission_classes = [IsPmUser]

    def post(self, request):
        contract = get_object_or_404(Contract, id=request.data['contract'])
        can = contract_can(contract=contract, user=request.user)
        if request.user.groups.filter(name='contract-admin').exists() or can['edit']:

            if request.data['f_proposal'] == 'removed':
                contract.f_proposal = None
            if request.data['f_acquittance'] == 'removed':
                contract.f_acquittance = None
            if request.data['f_draft'] == 'removed':
                contract.f_draft = None
            if request.data['f_contract'] == 'removed':
                contract.f_contract = None
            if request.data['f_warranty'] == 'removed':
                contract.f_warranty = None
            if request.data['f_technical_attachment'] == 'removed':
                contract.f_technical_attachment = None
            if request.data['f_non_disclosure_agreement'] == 'removed':
                contract.f_non_disclosure_agreement = None
            if request.data['f_exchange_letter'] == 'removed':
                contract.f_exchange_letter = None
            if request.data['f_acquittance_letter'] == 'removed':
                contract.f_acquittance_letter = None
            if request.data['f_statute'] == 'removed':
                contract.f_statute = None
            if request.data['f_newspaper'] == 'removed':
                contract.f_newspaper = None
            if request.data['f_etc1'] == 'removed':
                contract.f_etc1 = None
            if request.data['f_etc2'] == 'removed':
                contract.f_etc2 = None
            if request.data['f_etc3'] == 'removed':
                contract.f_etc3 = None

            if 'f_proposal2' in request.data:
                contract.f_proposal = request.data['f_proposal2']
            if 'f_acquittance2' in request.data:
                contract.f_acquittance = request.data['f_acquittance2']
            if 'f_draft2' in request.data:
                contract.f_draft = request.data['f_draft2']
            if 'f_contract2' in request.data:
                contract.f_contract = request.data['f_contract2']
            if 'f_warranty2' in request.data:
                contract.f_warranty = request.data['f_warranty2']
            if 'f_technical_attachment2' in request.data:
                contract.f_technical_attachment = request.data['f_technical_attachment2']
            if 'f_non_disclosure_agreement2' in request.data:
                contract.f_non_disclosure_agreement = request.data['f_non_disclosure_agreement2']
            if 'f_exchange_letter2' in request.data:
                contract.f_exchange_letter = request.data['f_exchange_letter2']
            if 'f_acquittance_letter2' in request.data:
                contract.f_acquittance_letter = request.data['f_acquittance_letter2']
            if 'f_statute2' in request.data:
                contract.f_statute = request.data['f_statute2']
            if 'f_newspaper2' in request.data:
                contract.f_newspaper = request.data['f_newspaper2']
            if 'f_etc12' in request.data:
                contract.f_etc1 = request.data['f_etc12']
            if 'f_etc22' in request.data:
                contract.f_etc2 = request.data['f_etc22']
            if 'f_etc32' in request.data:
                contract.f_etc3 = request.data['f_etc32']

            contract.save()
            data = SerContractDetail(instance=contract).data
            data['can'] = can
            return Response(data=data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class AddOrUpdateParty(GenericAPIView):
    permission_classes = [IsPmUser]

    def post(self, request):
        contract = get_object_or_404(Contract, id=request.data['contract'])
        can = contract_can(contract=contract, user=request.user)
        if request.user.groups.filter(name='contract-admin').exists() or can['edit']:
            if int(request.data['id']):
                party = contract.parties.get(pk=request.data['id'])
            else:
                party = contract.parties.create(name=request.data['name'])

            party.name = request.data['name']
            if request.data['f_nc'] == 'removed':
                party.f_nc = None
            if request.data['f_bc'] == 'removed':
                party.f_bc = None
            if request.data['f_d'] == 'removed':
                party.f_d = None
            if request.data['f_msc'] == 'removed':
                party.f_msc = None

            if 'f_nc2' in request.data:
                party.f_nc = request.data['f_nc2']
            if 'f_bc2' in request.data:
                party.f_bc = request.data['f_bc2']
            if 'f_d2' in request.data:
                party.f_d = request.data['f_d2']
            if 'f_msc2' in request.data:
                party.f_msc = request.data['f_msc2']

            party.save()
            data = SerContractDetail(instance=contract).data
            data['can'] = can
            return Response(data=data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class RemoveParty(GenericAPIView):
    permission_classes = [IsPmUser]

    def post(self, request):
        party = get_object_or_404(ContractParty, id=request.data['id'])
        contract = party.contract
        can = contract_can(contract=contract, user=request.user)
        if request.user.groups.filter(name='contract-admin').exists() or can['edit']:
            party.delete()
            data = SerContractDetail(instance=contract).data
            data['can'] = can
            return Response(data=data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class SaveContractSteps(GenericAPIView):
    permission_classes = [IsPmUser]

    def post(self, request):
        contract = get_object_or_404(Contract, id=request.data['id'])
        if contract_can(contract=contract, user=request.user)['edit']:
            ids = list(map(lambda p: p['id'], request.data['steps']))
            contract.steps.exclude(id__in=ids).delete()
            for item in request.data['steps']:
                if item['id']:
                    step = get_object_or_404(Step, id=item['id'], contract=contract)
                    step.title = item['title']
                    step.price = round(item['percent'] * contract.price / 100)
                    step.start_date = item['start_date']
                    step.finish_date = item['finish_date']
                    step.save()
                else:
                    Step.objects.create(contract=contract, title=item['title'], price=round(item['percent'] * contract.price / 100), start_date=item['start_date'], finish_date=item['finish_date'])
        return Response(data=SerStep(contract.steps.all(), many=True).data)


class SaveContractSupplements(GenericAPIView):
    permission_classes = [IsPmUser]

    def post(self, request):
        if not request.user.groups.filter(name='contract-admin').exists():
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        contract = get_object_or_404(Contract, id=request.data['id'])
        ids = list(map(lambda p: p['id'], request.data['supplements']))
        contract.supplements.exclude(id__in=ids).delete()
        for item in request.data['supplements']:
            if item['id']:
                supplement = get_object_or_404(Supplement, id=item['id'], contract=contract)
                supplement.no = item['no']
                supplement.date = item['date']
                supplement.description = item['description']
            else:
                supplement = Supplement.objects.create(contract=contract, no=item['no'], date=item['date'], description=item['description'])
            if 'price' in item and item['price']:
                supplement.price = item['price']
            else:
                supplement.price = None
            if 'start_date' in item and item['start_date']:
                supplement.start_date = item['start_date']
            else:
                supplement.start_date = None
            if 'finish_date' in item and item['finish_date']:
                supplement.finish_date = item['finish_date']
            else:
                supplement.finish_date = None
            supplement.save()
        return Response(data=SerSupplement(contract.supplements.all(), many=True).data)


class ContractTaskList(GenericAPIView):
    def get(self, request, no):
        contract = get_object_or_404(Contract, no=no)
        if contract_can(contract, request.user)['see']:
            return Response(data=SerContractTask(contract.tasks, many=True).data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class DoContractAction(GenericAPIView):
    """فرآیند تصویب قرارداد"""
    def post(self, request):
        user = request.user
        contract = get_object_or_404(Contract, id=request.data['id'])
        can = contract_can(contract, user)
        next_group = 'none'
        next_title = ''
        next_user = None
        action = request.data['title']
        match action:

            case 'ارسال قرارداد':
                if not can['edit']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.locked = True
                if contract.head_accept == 'عودت جهت اصلاح':
                    contract.head_accept = 'نامشخص'
                    next_group = 'contract-head-accept'
                elif contract.deputy_accept == 'عودت جهت اصلاح':
                    contract.deputy_accept = 'نامشخص'
                    next_group = 'contract-deputy-accept'
                elif contract.committee_accept == 'عودت جهت اصلاح':
                    contract.committee_accept = 'نامشخص'
                    next_group = 'contract-committee-accept'
                elif contract.convention_accept == 'عودت جهت اصلاح':
                    contract.convention_accept = 'نامشخص'
                    next_group = 'contract-admin'
                elif contract.fund_accept == 'عودت جهت اصلاح':
                    contract.fund_accept = 'نامشخص'
                    next_group = 'contract-fund-accept'
                else:
                    contract.manager_accept = 'نامشخص'
                    next_user = contract.project.unit.manager
                contract.save()
                next_title = 'بررسی قرارداد'

            case 'تأیید مدیر واحد':
                if not can['manager_accept']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.manager_accept = request.data['answer']
                if contract.manager_accept == 'تأیید':
                    next_title = 'بررسی قرارداد'
                    next_group = 'contract-fund-accept'
                elif contract.manager_accept == 'عودت جهت اصلاح':
                    next_title = 'اصلاح قرارداد'
                    next_user = contract.registrar
                    contract.locked = False
                contract.save()

            case 'تأیید واحد بودجه':
                if not can['fund_accept']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.fund_accept = request.data['answer']
                if contract.fund_accept == 'تأیید':
                    next_title = 'بررسی قرارداد'
                    next_group = 'contract-admin'
                elif contract.fund_accept == 'عودت جهت اصلاح':
                    next_title = 'اصلاح قرارداد'
                    next_user = contract.registrar
                    contract.locked = False
                contract.save()

            case 'تأیید واحد قراردادها':
                if not can['convention_accept']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.convention_accept = request.data['answer']
                if contract.convention_accept == 'تأیید':
                    contract.need_committee = request.data['check'] == 'true'
                    next_title = 'بررسی قرارداد'
                    if contract.need_committee:
                        next_group = 'contract-committee-accept'
                    else:
                        next_group = 'contract-deputy-accept'
                        contract.committee_accept = 'تأیید'
                elif contract.convention_accept == 'عودت جهت اصلاح':
                    next_title = 'اصلاح قرارداد'
                    next_user = contract.registrar
                    contract.locked = False
                contract.save()

            case 'تأیید کمیته پژوهش':
                if not can['committee_accept']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.committee_accept = request.data['answer']
                if contract.committee_accept == 'تأیید':
                    next_title = 'تهیه پیشنویس'
                    next_group = 'contract-admin'
                    contract.deputy_accept = 'تأیید'
                    contract.head_accept = 'تأیید'
                elif contract.committee_accept == 'عودت جهت اصلاح':
                    next_title = 'اصلاح قرارداد'
                    next_user = contract.registrar
                    contract.locked = False
                contract.save()

            case 'تأیید معاون توسعه':
                if not can['deputy_accept']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.deputy_accept = request.data['answer']
                if contract.deputy_accept == 'تأیید':
                    next_title = 'بررسی قرارداد'
                    next_group = 'contract-head-accept'
                elif contract.deputy_accept == 'عودت جهت اصلاح':
                    next_title = 'اصلاح قرارداد'
                    next_user = contract.registrar
                    contract.locked = False
                contract.save()

            case 'تأیید رئیس مرکز':
                if not can['head_accept']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.head_accept = request.data['answer']
                if contract.head_accept == 'تأیید':
                    next_title = 'تهیه پیشنویس'
                    next_group = 'contract-admin'
                elif contract.head_accept == 'عودت جهت اصلاح':
                    next_title = 'اصلاح قرارداد'
                    next_user = contract.registrar
                    contract.locked = False
                contract.save()

            case 'تهیه پیشنویس':
                if not can['draft']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                if contract.f_draft in ['', None]:
                    return Response(data='فایل پیشنویس به قرارداد الصاق نشده است', status=status.HTTP_400_BAD_REQUEST)
                contract.drafted = True
                contract.draft_accept = None
                contract.save()
                next_title = 'بررسی پیشنویس'
                next_user = contract.project.unit.manager

            case 'تأیید پیشنویس':
                if not can['draft_accept']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.draft_accept = request.data['answer'] == 'تأیید'
                if contract.draft_accept:
                    next_title = 'ارسال برای پیمانکار'
                else:
                    next_title = 'اصلاح پیشنویس'
                    contract.drafted = False
                contract.save()
                next_group = 'contract-admin'

            case 'ارسال قرارداد برای پیمانکار':
                if not can['send_to_contractor']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.send_to_contractor_date = jdatetime.datetime.now().date()
                contract.save()
                next_title = 'دریافت قرارداد از پیمانکار'
                next_group = 'contract-admin'

            case 'دریافت قرارداد از پیمانکار':
                if not can['receive_from_contractor']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.receive_from_contractor_date = jdatetime.datetime.now().date()
                contract.save()
                next_title = 'امضای مقام مجاز'
                next_group = 'contract-admin'

            case 'امضای مقام مجاز':
                if not can['signature']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.signature_date = jdatetime.datetime.now().date()
                contract.save()
                next_title = 'ثبت در دبیرخانه'
                next_group = 'contract-admin'

            case 'ثبت در دبیرخانه':
                if not can['secretariat']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.secretariat_date = jdatetime.datetime.now().date()
                contract.secretariat_no = request.data['answer']
                contract.save()
                next_title = 'تعیین نوع ضمانتنامه'
                next_group = 'contract-warranty-select'

            case 'تعیین نوع ضمانتنامه':
                if not can['warranty_type']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.warranty_type = request.data['answer']
                contract.save()
                next_title = 'الصاق ضمانتنامه'
                next_group = 'contract-warranty-add'

            case 'الصاق ضمانتنامه':
                if not can['f_warranty']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.f_warranty = request.data['file']
                if 'warranty_start_date' in request.data:
                    contract.warranty_start_date = request.data['warranty_start_date']
                if 'warranty_end_date' in request.data:
                    contract.warranty_end_date = request.data['warranty_end_date']
                contract.save()
                next_title = 'الصاق مفاصا'
                next_group = 'contract-warranty-add'

            case 'الصاق مفاصا':
                if not can['f_warranty']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.f_acquittance = request.data['file']
                contract.save()

            case 'بایگانی قرارداد':
                if not can['archive']:
                    return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
                contract.archived = True
                contract.save()

        contract.tasks.create(status=request.data['title'], answer=request.data['answer'], user=user, note=request.data['note'])
        for u in User.objects.filter(groups__name=next_group):
            u.notifications.create(title=next_title, body=contract.title, url=f'/contract/{contract.no}', contract=contract)
        if next_user:
            next_user.notifications.create(title=next_title, body=contract.title, url=f'/contract/{contract.no}', contract=contract)
        # اطلاع مراحل پیشرفت قرارداد به مدیر واحد
        if action not in ['ارسال قرارداد', 'تأیید مدیر واحد']:
            Notification.objects.create(user=contract.project.unit.manager, title=f'فرآیند قرارداد {contract.no}', body=f'مرحله {action} انجام شد', url=f'/contract/{contract.no}', contract=contract)
        data = SerContractDetail(instance=contract).data
        data['can'] = contract_can(contract, request.user)
        return Response(data={'contract': data, 'todo_contract': request.user.todo_contract})


class RemoveContract(DestroyAPIView):
    permission_classes = [IsPmUser]

    def get_object(self):
        contract = get_object_or_404(Contract, id=self.kwargs['pk'])
        return contract if contract_can(contract, self.request.user)['edit'] else None


class AddOrEditPay(GenericAPIView):
    permission_classes = [IsPmUser]

    def post(self, request):
        pk = int(request.data.get('id', 0))
        user = request.user
        if pk:
            pay = get_object_or_404(Pay, pk=pk, step__contract__project__unit_id=user.post.unit_id, locked=False)
            pay.bill_requested = request.data['bill_requested']
            pay.note = request.data['note']
            if 'file' in request.data:
                pay.file = request.data['file']
            if pay.audit == 'عودت جهت اصلاح':
                pay.audit = 'نامشخص'
            elif pay.finance_accept == 'عودت جهت اصلاح':
                pay.finance_accept = 'نامشخص'
            elif pay.head_accept == 'عودت جهت اصلاح':
                pay.head_accept = 'نامشخص'
            elif pay.deputy_accept == 'عودت جهت اصلاح':
                pay.deputy_accept = 'نامشخص'
            elif pay.deputy_accept == 'عودت جهت اصلاح':
                pay.deputy_accept = 'نامشخص'
            elif pay.clerk_accept == 'عودت جهت اصلاح':
                pay.clerk_accept = 'نامشخص'
            elif pay.fund_accept == 'عودت جهت اصلاح':
                pay.fund_accept = 'نامشخص'
            elif pay.convention_accept == 'عودت جهت اصلاح':
                pay.convention_accept = 'نامشخص'
            else:
                pay.manager_accept = 'نامشخص'
            pay.locked = True
            pay.save()
            pay.tasks.create(status='اصلاح درخواست', user=request.user, note=request.data['note'])
        else:
            pay = user.pays.create(step_id=request.data['step'], bill_requested=request.data['bill_requested'], note=request.data['note'], file=request.data['file'])
            pay.tasks.create(status='ثبت درخواست', user=request.user, note=request.data['note'])
        return Response(data=SerPayList(pay).data)


class DoPayAction(GenericAPIView):
    permission_classes = [IsPmUser]

    def post(self, request):
        pay = get_object_or_404(Pay, id=request.data['id'])
        user = request.user
        if pay_can(pay, user)['manager_accept']:
            _status = 'نظر مدیر واحد'
            answer = request.data['manager_accept']
            pay.manager_accept = request.data['manager_accept']
            if pay.manager_accept == 'عودت جهت اصلاح':
                pay.locked = False
        elif pay_can(pay, user)['convention_accept']:
            _status = 'نظر واحد قراردادها'
            answer = request.data['convention_accept']
            pay.convention_accept = request.data['convention_accept']
            if pay.convention_accept == 'عودت جهت اصلاح':
                pay.locked = False
        elif pay_can(pay, user)['fund_accept']:
            _status = 'نظر واحد بودجه'
            answer = request.data['fund_accept']
            pay.fund_accept = request.data['fund_accept']
            if pay.fund_accept == 'عودت جهت اصلاح':
                pay.locked = False
        elif pay_can(pay, user)['clerk_accept']:
            _status = 'نظر کارشناس مالی'
            answer = request.data['clerk_accept']
            pay.clerk_accept = request.data['clerk_accept']
            if pay.clerk_accept == 'عودت جهت اصلاح':
                pay.locked = False
        elif pay_can(pay, user)['deputy_accept']:
            _status = 'نظر معاون توسعه'
            answer = request.data['deputy_accept']
            pay.deputy_accept = request.data['deputy_accept']
            pay.need_head = request.data['need_head'] == 'true'
            if pay.deputy_accept == 'عودت جهت اصلاح':
                pay.locked = False
        elif pay_can(pay, user)['head_accept']:
            _status = 'نظر رئیس مرکز'
            answer = request.data['head_accept']
            pay.head_accept = request.data['head_accept']
            if pay.head_accept == 'عودت جهت اصلاح':
                pay.locked = False
        elif pay_can(pay, user)['finance_accept']:
            _status = 'نظر مدیرکل مالی'
            answer = request.data['finance_accept']
            pay.finance_accept = request.data['finance_accept']
            if pay.finance_accept == 'عودت جهت اصلاح':
                pay.locked = False
        elif pay_can(pay, user)['audit']:
            _status = 'ممیزی'
            answer = request.data['audit']
            pay.audit = request.data['audit']
            # ممکن است ممیزی منفی باشد و ارقام مالیات و... ارسال نشود
            pay.tax = request.data.get('tax', 0)
            pay.insurance = request.data.get('insurance', 0)
            pay.commitments = request.data.get('commitments', 0)
            pay.value_added = request.data.get('value_added', 0)
            pay.net = request.data.get('net', 0)
            if pay.audit == 'عودت جهت اصلاح':
                pay.locked = False
        elif pay_can(pay, user)['pay']:
            _status = 'پرداخت'
            answer = 'پرداخت شد' if request.data['paid'] == 'true' else 'پرداخت نشد'
            pay.paid = request.data['paid'] == 'true'
            if pay.paid and 'file' in request.data:
                pay.slip = request.data['file']
        else:
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        pay.save()
        pay.tasks.create(user=user, status=_status, answer=answer, note=request.data['note'])
        return Response(data=SerPayList(pay).data)


class PayList(GenericAPIView):
    permission_classes = [IsPmUser]

    def get(self, request):
        if request.GET.get('need_action', 'همه') == 'منتظر اقدام':
            pay_list = request.user.todo_pay_list()
        elif request.user.groups.filter(name__in=['supervisor', 'contract-admin', 'contract-deputy-accept', 'contract-head-accept', 'contract-fund-accept', 'contract-warranty-add', 'contract-warranty-select', 'contract-pay-pay']).exists():
            pay_list = Pay.objects.all()
        else:
            pay_list = Pay.objects.filter(step__contract__project__unit=request.user.post.unit)
        pay_list = pay_list.select_related('step', 'step__contract', 'step__contract__project', 'step__contract__project__unit')

        department = int(request.GET.get('department', 0))
        contract = int(request.GET.get('contract', 0))
        order = request.GET.get('order', 'تاریخ ثبت')
        q = request.GET.get('q', None)
        manager_accept = request.GET.get('manager_accept', 'همه')
        convention_accept = request.GET.get('convention_accept', 'همه')
        fund_accept = request.GET.get('fund_accept', 'همه')
        deputy_accept = request.GET.get('deputy_accept', 'همه')
        head_accept = request.GET.get('head_accept', 'همه')
        finance_accept = request.GET.get('finance_accept', 'همه')
        paid = request.GET.get('paid', 'همه')

        if department:
            pay_list = pay_list.filter(Q(step__contract__project__unit_id=department) | Q(step__contract__project__unit__parent_id=department))
        if contract:
            pay_list = pay_list.filter(step__contract_id=contract)
        if q:
            q_list = q.split(' ')
            q_filter = reduce(operator.and_, (Q(step__contract__project__title__contains=q_text) | Q(step__contract__title__contains=q_text) | Q(step__contract__tags__icontains=q_text) | Q(step__contract__contractor__contains=q_text) | Q(step__contract__cn_note__contains=q_text) | Q(step__contract__no__contains=q_text) for q_text in q_list))
            pay_list = pay_list.filter(q_filter)
        if manager_accept != 'همه':
            pay_list = pay_list.filter(manager_accept=manager_accept)
        if convention_accept != 'همه':
            pay_list = pay_list.filter(convention_accept=convention_accept)
        if fund_accept != 'همه':
            pay_list = pay_list.filter(fund_accept=fund_accept)
        if deputy_accept != 'همه':
            pay_list = pay_list.filter(deputy_accept=deputy_accept)
        if head_accept != 'همه':
            pay_list = pay_list.filter(head_accept=head_accept)
        if finance_accept != 'همه':
            pay_list = pay_list.filter(finance_accept=finance_accept)
        if paid != 'همه':
            pay_list = pay_list.filter(paid=None if paid == 'درانتظار پرداخت' else paid == 'پرداخت شد')

        size = request.user.profile.page_size
        page = min(int(request.GET.get('page', 1)), pay_list.count() // size + 1)
        pay_list = pay_list.order_by('-create_time' if order == 'تاریخ' else 'step__contract_id')
        data = {
            'count': pay_list.count(),
            'requested': pay_list.aggregate(val=Sum('bill_requested'))['val'] or 0,
            'paid': pay_list.aggregate(val=Sum('bill', filter=Q(paid=True)))['val'] or 0,
            'page': page,
            'size': size,
            'list': SerPayList(instance=pay_list[size*(page-1):size*page], many=True).data
        }
        return Response(data=data)


class PayDetail(GenericAPIView):
    def get(self, request, pk):
        pay = get_object_or_404(Pay, id=pk)
        can = pay_can(pay, request.user)
        if not can['see']:
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        data = SerPayDetail(instance=pay).data
        data['can'] = can
        request.user.notifications.filter(pay=pay).update(seen_time=jdatetime.datetime.now())
        return Response(data=data)


class ContractListInDepartment(ListAPIView):
    permission_classes = [IsPmUser]
    serializer_class = SerSimpleContractList

    def get_queryset(self):
        if int(self.kwargs['pk']):
            return Contract.objects.filter(secretariat_date__isnull=False).filter(Q(project__unit_id=self.kwargs['pk']) | Q(project__unit__parent_id=self.kwargs['pk']))
        return Contract.objects.filter(secretariat_date__isnull=False).filter(Q(project__unit=self.request.user.post.unit) | Q(project__unit__parent=self.request.user.post.unit))


class StepListInContract(ListAPIView):
    permission_classes = [IsPmUser]
    serializer_class = SerStep

    def get_queryset(self):
        return Step.objects.filter(contract_id=self.kwargs['pk'])


class PayTaskList(ListAPIView):
    permission_classes = [IsPmUser]
    serializer_class = SerPayTask

    def get_queryset(self):
        pay = get_object_or_404(Pay, id=self.kwargs['pk'])
        return pay.tasks.all()


class RemovePay(DestroyAPIView):
    permission_classes = [IsPmUser]

    def get_object(self):
        pay = get_object_or_404(Pay, id=self.kwargs['pk'], registrar=self.request.user)
        return pay if pay.locked is False or pay.manager_accept == 'نامشخص' else None


class ToggleInquiryStatus(GenericAPIView):
    def post(self, request):
        if not request.user.groups.filter(name='contract-admin').exists():
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        contract = get_object_or_404(Contract, id=request.data['contract'])
        contract.inquiry = request.data['inquiry']
        contract.save()
        return Response()


class ToggleCnNote(GenericAPIView):
    def post(self, request):
        if not request.user.groups.filter(name='contract-admin').exists():
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        contract = get_object_or_404(Contract, id=request.data['contract'])
        contract.cn_note = request.data['note']
        contract.save()
        return Response()


# ########## پایگاه دانش ##########


class ArticleCategoryList(ListAPIView):
    queryset = ArticleCategory.objects.filter(parent=None)
    serializer_class = SerArticleCategoryList

    def get_serializer_context(self):
        context = super(ArticleCategoryList, self).get_serializer_context()
        context.update({'user': self.request.user})
        return context


class ArticleCategoryDetail(RetrieveAPIView):
    serializer_class = SerArticleCategoryDetail
    queryset = ArticleCategory.objects.all()

    def get_serializer_context(self):
        context = super(ArticleCategoryDetail, self).get_serializer_context()
        context.update({'user': self.request.user})
        return context


class ArticleDetail(RetrieveDestroyAPIView):
    serializer_class = SerArticleDetail
    queryset = Article.objects.all()

    def get_object(self):
        article = super(ArticleDetail, self).get_object()
        if article.is_available or self.request.user in article.category.owners.all():
            return article
        return None

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context


class RateArticle(GenericAPIView):
    def post(self, request):
        article = get_object_or_404(Article, id=request.data['id'], is_available=True)
        rate = article.rates.filter(user=request.user).first()
        if rate:
            rate.rate = request.data['rate']
            rate.save()
        else:
            article.rates.create(user=request.user, rate=request.data['rate'])
        return Response(data=article.rate)


class ArticleAttachmentDownload(GenericAPIView):
    def get(self, request, pk):
        attachment = get_object_or_404(ArticleAttachment, pk=pk)
        if request.user in attachment.article.category.owners.all() or ArticlePermit.objects.filter(article_id=attachment.article_id, user=request.user, accept=True).exists():
            return FileResponse(attachment.file)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class ArticlePermitRequest(GenericAPIView):
    def post(self, request):
        article = get_object_or_404(Article, id=request.data['id'], is_available=True)
        permit = article.permits.filter(user=request.user).exclude(accept=True).first()
        if permit:
            permit.note = request.data['note']
            permit.accept = None
            permit.save()
        else:
            permit = article.permits.create(user=request.user, note=request.data['note'])
        return Response(data=SerArticlePermit(permit).data)


class ArticleChatAdd(GenericAPIView):
    def post(self, request):
        chat = ArticleChat.objects.create(article_id=request.data['article'], body=request.data['body'], user=request.user)
        return Response(data=SerArticleChat(chat, context={'user': request.user}).data)


class ArticleChatLike(GenericAPIView):
    def post(self, request):
        chat = get_object_or_404(ArticleChat, id=request.data['chat'])
        like = chat.likes.get_or_create(user=request.user)[0]
        like.like = request.data['like']
        like.save()
        return Response(data={
            'yes': chat.likes.filter(like=True).count(),
            'no': chat.likes.filter(like=False).count(),
            'my': like.like
        })


class ArticlePermRequestList(GenericAPIView):
    def get(self, request, pk):
        category = get_object_or_404(ArticleCategory, id=pk, owners__in=[request.user])
        permits = ArticlePermit.objects.filter(article__category=category, accept=None)
        return Response(SerArticlePermit(permits, many=True).data)


class ArticlePermitAccept(GenericAPIView):
    def post(self, request):
        permit = get_object_or_404(ArticlePermit, id=request.data['permit'], accept=None, article__category__owners__in=[request.user])
        permit.accept = request.data['accept']
        permit.save()
        return Response()


class ArticleSave(GenericAPIView):
    def post(self, request):
        data = json.loads(request.data['data'])
        if data['id']:
            article = get_object_or_404(Article, id=data['id'], category__owners=request.user)
            article.step_id = data['step']
            article.title = data['title']
            article.subtitle = data['subtitle']
            article.tags = data['tags']
            article.summary = data['summary']
            article.is_available = data['is_available']
            if 'poster' in request.data:
                article.poster = request.data['poster']
            article.save()
        else:
            article = Article.objects.create(user=request.user, unit=request.user.post.unit, category_id=data['category'], step_id=data['step'], title=data['title'], subtitle=data['subtitle'], tags=data['tags'], poster=request.data['poster'], summary=data['summary'], is_available=data['is_available'])
        pks = []
        for item in data['attachments']:
            if item['id']:
                attachment = get_object_or_404(ArticleAttachment, id=item['id'], article=article)
                attachment.title = item['title']
                attachment.author = item['author']
                attachment.save()
                pks.append(attachment.id)
            else:
                attachment = article.attachments.create(title=item['title'], author=item['author'], file=request.data[f'file{item["index"]}'])
                pks.append(attachment.id)
        article.attachments.exclude(id__in=pks).delete()
        return Response(SerArticleDetail(article, context={'user': request.user}).data)


class ArticlePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ArticleListAPI(ListAPIView):
    queryset = Article.objects.filter(is_available=True).select_related('category', 'unit', 'step')
    serializer_class = SerArticleList
    pagination_class = ArticlePagination
    # اضافه کردن فیلتر و مرتب‌سازی
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    # فیلدهایی که می‌خوایم فیلتر کنیم
    filterset_fields = {
        'category': ['exact'],      # فیلتر بر اساس category
        'user': ['exact'],          # فیلتر بر اساس کاربر
        'unit': ['exact'],          # فیلتر بر اساس واحد
        'step': ['exact'],          # فیلتر بر اساس step
        'create_time': ['gte', 'lte'],  # فیلتر بر اساس بازه زمانی
    }

    # فیلدهایی که می‌خوایم جستجو کنیم
    search_fields = ['title', 'subtitle', 'summary', 'tags']

    # فیلدهای مرتب‌سازی پیش‌فرض
    ordering_fields = ['create_time', 'update_time', 'title']
    ordering = ['create_time']