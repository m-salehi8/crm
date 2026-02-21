from rest_framework import serializers
from django_jalali.serializers.serializerfield import JDateField
from .models import *


class SerAgreement(serializers.ModelSerializer):
    class Meta:
        model = Agreement
        fields = '__all__'


class SerContractList(serializers.ModelSerializer):
    project_title = serializers.CharField(read_only=True, source='project.title')
    department = serializers.IntegerField(read_only=True, source='project.unit.department.id')
    department_title = serializers.CharField(read_only=True, source='project.unit.department.title')
    start_date = JDateField(allow_null=True)
    finish_date = JDateField(allow_null=True)

    class Meta:
        model = Contract
        fields = ['id', 'registrar', 'no', 'type', 'genre', 'contractor', 'contractor_no', 'title', 'start_date', 'finish_date', 'price', '_start_date', '_finish_date', '_price', 'sum_of_pay', 'period', 'status', 'project', 'project_title', 'department', 'department_title', 'has_value_added',
                  'locked', 'manager_accept', 'fund_accept', 'convention_accept', 'need_committee', 'committee_accept', 'deputy_accept', 'head_accept', 'drafted', 'draft_accept', 'send_to_contractor_date', 'receive_from_contractor_date', 'signature_date', 'secretariat_date', 'warranty_type', 'f_warranty', 'f_acquittance', 'archived', 'tags', 'agreement']


class SerStep(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ['id', 'title', 'contract', 'price', 'percent', 'pay', 'start_date', 'finish_date']


class SerContractParty(serializers.ModelSerializer):
    user_name = serializers.CharField(read_only=True, source='user.get_full_name')
    f_nc = serializers.CharField(read_only=True, source='f_nc.name')
    f_bc = serializers.CharField(read_only=True, source='f_bc.name')
    f_d = serializers.CharField(read_only=True, source='f_d.name')
    f_msc = serializers.CharField(read_only=True, source='f_msc.name')

    class Meta:
        model = ContractParty
        fields = ['id', 'user_name', 'name', 'f_nc', 'f_bc', 'f_d', 'f_msc']


class SerPayList(serializers.ModelSerializer):
    step_title = serializers.CharField(read_only=True, source='step.title')
    unit = serializers.IntegerField(read_only=True, source='step.contract.project.unit.id')
    department = serializers.CharField(read_only=True, source='step.contract.project.unit.department.title')
    project = serializers.IntegerField(read_only=True, source='step.contract.project.id')
    project_title = serializers.CharField(read_only=True, source='step.contract.project.title')
    contract_no = serializers.IntegerField(read_only=True, source='step.contract.no')
    contract_title = serializers.CharField(read_only=True, source='step.contract.title')

    class Meta:
        model = Pay
        fields = ['id', 'registrar', 'unit', 'department', 'project', 'project_title', 'contract_no', 'contract_title', 'step_title', 'bill_requested', 'date', 'bill', 'locked', 'status']


class SerPayDetail(serializers.ModelSerializer):
    step_title = serializers.CharField(read_only=True, source='step.title')
    step_price = serializers.IntegerField(read_only=True, source='step.price')
    department = serializers.IntegerField(read_only=True, source='step.contract.project.unit.department.id')
    department_title = serializers.CharField(read_only=True, source='step.contract.project.unit.department.title')
    project = serializers.IntegerField(read_only=True, source='step.contract.project.id')
    project_title = serializers.CharField(read_only=True, source='step.contract.project.title')
    contract = serializers.IntegerField(read_only=True, source='step.contract.id')
    contract_no = serializers.IntegerField(read_only=True, source='step.contract.no')
    contract_title = serializers.CharField(read_only=True, source='step.contract.title')

    class Meta:
        model = Pay
        fields = ['id', 'registrar', 'department', 'department_title', 'project', 'project_title', 'contract', 'contract_no', 'contract_title',
                  'step', 'step_title', 'step_price', 'percent_requested', 'percent', 'bill_requested', 'bill', 'date', 'note', 'file_url',
                  'locked', 'manager_accept', 'convention_accept', 'fund_accept', 'clerk_accept', 'deputy_accept', 'need_head', 'head_accept', 'finance_accept', 'audit', 'paid',
                  'tax', 'insurance', 'commitments', 'value_added', 'net', 'status', 'slip_url']


class SerSupplement(serializers.ModelSerializer):
    date = JDateField()
    start_date = JDateField()
    finish_date = JDateField()

    class Meta:
        model = Supplement
        fields = ['id', 'contract', 'no', 'date', 'price', 'start_date', 'finish_date', 'description']


class SerContractDetail(serializers.ModelSerializer):
    registrar_name = serializers.CharField(read_only=True, source='registrar.get_full_name')
    project_title = serializers.CharField(read_only=True, source='project.title')
    unit = serializers.IntegerField(read_only=True, source='project.unit_id')
    department = serializers.IntegerField(read_only=True, source='project.unit.department.id')
    department_title = serializers.CharField(read_only=True, source='project.unit.department.title')
    start_date = JDateField()
    finish_date = JDateField()
    steps = SerStep(read_only=True, many=True)
    parties = SerContractParty(read_only=True, many=True)
    pays = serializers.SerializerMethodField()
    supplements = SerSupplement(read_only=True, many=True)
    f_proposal = serializers.CharField(read_only=True, source='f_proposal.name')
    f_acquittance = serializers.CharField(read_only=True, source='f_acquittance.name')
    f_draft = serializers.CharField(read_only=True, source='f_draft.name')
    f_contract = serializers.CharField(read_only=True, source='f_contract.name')
    f_warranty = serializers.CharField(read_only=True, source='f_warranty.name')
    f_technical_attachment = serializers.CharField(read_only=True, source='f_technical_attachment.name')
    f_non_disclosure_agreement = serializers.CharField(read_only=True, source='f_non_disclosure_agreement.name')
    f_exchange_letter = serializers.CharField(read_only=True, source='f_exchange_letter.name')
    f_acquittance_letter = serializers.CharField(read_only=True, source='f_acquittance_letter.name')
    f_statute = serializers.CharField(read_only=True, source='f_statute.name')
    f_newspaper = serializers.CharField(read_only=True, source='f_newspaper.name')
    f_etc1 = serializers.CharField(read_only=True, source='f_etc1.name')
    f_etc2 = serializers.CharField(read_only=True, source='f_etc2.name')
    f_etc3 = serializers.CharField(read_only=True, source='f_etc3.name')

    def get_pays(self, contract):
        return SerPayList(instance=Pay.objects.filter(step__contract=contract).order_by('step'), many=True).data

    class Meta:
        model = Contract
        fields = ['id', 'registrar', 'registrar_name', 'project', 'project_title', 'unit', 'no', 'type', 'genre', 'contractor', 'contractor_no', 'title', 'note', 'agreement',
                  'locked', 'manager_accept', 'fund_accept', 'convention_accept', 'need_committee', 'committee_accept', 'deputy_accept', 'head_accept', 'drafted', 'draft_accept',
                  'send_to_contractor_date', 'receive_from_contractor_date', 'signature_date', 'secretariat_date', 'secretariat_no', 'warranty_type', 'warranty_start_date', 'warranty_end_date', 'has_value_added',
                  'tags', 'cn_note', 'start_date', 'finish_date', 'period', 'price', '_start_date', '_finish_date', '_price', 'status', 'body', 'department', 'department_title',
                  'sum_of_pay', 'steps', 'parties', 'pays', 'supplements', 'f_proposal', 'f_acquittance', 'f_draft', 'f_contract', 'f_warranty', 'f_technical_attachment',
                  'f_non_disclosure_agreement', 'f_exchange_letter', 'f_acquittance_letter', 'f_statute', 'f_newspaper', 'f_etc1', 'f_etc2', 'f_etc3']


class SerContractTask(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source='user.get_full_name')

    class Meta:
        model = ContractTask
        fields = ['id', 'contract', 'status', 'answer', 'user', '_time', 'note']


class SerSimpleContractList(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['id', 'title']


class SerPayTask(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source='user.get_full_name')

    class Meta:
        model = PayTask
        fields = ['id', 'status', 'answer', 'user', '_time', 'note']


# ########## پایگاه دانش ##########


class SerArticleCategoryList(serializers.ModelSerializer):
    class Meta:
        model = ArticleCategory
        fields = ['id', 'title', 'article_count', 'children']

    article_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    def get_article_count(self, category):
        return category.articles.count() if self.context['user'] in category.owners.all() else category.articles.filter(is_available=True).count()

    def get_children(self, category):
        return SerArticleCategoryList(instance=category.children.all(), many=True, context={'user': self.context['user']}).data


class SerArticleList(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'user', 'unit', 'unit_title', 'category', 'category_title', 'step', 'step_title', 'contract', 'contract_title', 'title', 'subtitle', 'tags', 'poster_url', 'summary', 'is_available', 'create_time', 'update_time', 'attachment_count', 'chat_count', 'permit_count', 'rate']

    unit_title = serializers.CharField(read_only=True, source='unit.title')
    category_title = serializers.CharField(read_only=True, source='category.title')
    step_title = serializers.CharField(read_only=True, source='step.title')
    contract = serializers.IntegerField(read_only=True, source='step.contract.id')
    contract_title = serializers.CharField(read_only=True, source='step.contract.title')


class SerArticleCategoryDetail(serializers.ModelSerializer):
    class Meta:
        model = ArticleCategory
        fields = ['id', 'title', 'description', 'owners', 'articles', 'request_count']

    articles = serializers.SerializerMethodField()
    request_count = serializers.SerializerMethodField()

    def get_articles(self, category):
        if self.context['user'] in category.owners.all():
            article_list = category.articles.all()
        else:
            article_list = category.articles.filter(is_available=True)
        return SerArticleList(article_list.select_related('unit', 'category', 'step', 'step__contract'), many=True).data

    def get_request_count(self, category):
        if self.context['user'] in category.owners.all():
            return ArticlePermit.objects.filter(article__category=category, accept=None).count()
        return 0


class SerArticleAttachment(serializers.ModelSerializer):
    class Meta:
        model = ArticleAttachment
        fields = ['id', 'title', 'author', 'create_time']


class SerArticlePermit(serializers.ModelSerializer):
    class Meta:
        model = ArticlePermit
        fields = ['id', 'article', 'article_title', 'user', 'user_name', 'unit', 'unit_title', 'note', 'accept', 'create_time']

    article_title = serializers.CharField(read_only=True, source='article.title')
    user_name = serializers.CharField(read_only=True, source='user.get_full_name')
    unit = serializers.CharField(read_only=True, source='user.post.unit.id')
    unit_title = serializers.CharField(read_only=True, source='user.post.unit.title')


class SerArticleChat(serializers.ModelSerializer):
    class Meta:
        model = ArticleChat
        fields = ['id', 'user', 'user_name', 'user_photo', 'body', 'create_time', 'like']

    user_name = serializers.CharField(read_only=True, source='user.get_full_name')
    user_photo = serializers.CharField(read_only=True, source='user.photo_url')
    like = serializers.SerializerMethodField()

    def get_like(self, chat):
        my_like = chat.likes.filter(user=self.context['user']).first()
        return {
            'yes': chat.likes.filter(like=True).count(),
            'no': chat.likes.filter(like=False).count(),
            'my': my_like.like if my_like else None,
        }


class SerArticleDetail(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'user', 'unit', 'unit_title', 'category', 'category_title', 'step', 'step_title', 'contract', 'contract_title', 'title', 'subtitle', 'tags', 'poster_url', 'summary', 'is_available', 'create_time', 'update_time', 'attachments', 'permit', 'rate', 'chats']

    unit_title = serializers.CharField(read_only=True, source='unit.title')
    category_title = serializers.CharField(read_only=True, source='category.title')
    step_title = serializers.CharField(read_only=True, source='step.title')
    contract = serializers.IntegerField(read_only=True, source='step.contract.id')
    contract_title = serializers.CharField(read_only=True, source='step.contract.title')
    attachments = SerArticleAttachment(read_only=True, many=True)
    permit = serializers.SerializerMethodField()
    chats = serializers.SerializerMethodField()

    def get_permit(self, article):
        p = article.permits.filter(user=self.context['user']).first()
        return {'accept': p.accept} if p else None

    def get_chats(self, article):
        return SerArticleChat(instance=article.chats.all(), many=True, context={'user': self.context['user']}).data
