from .models import *
from unfold.admin import ModelAdmin, TabularInline


@admin.register(Agreement)
class AgreementAdmin(ModelAdmin):
    list_display = ['title']
    search_fields = ['title']


class ContractTaskInline(TabularInline):
    model = ContractTask
    raw_id_fields = ['user']
    extra = 0


class StepInline(TabularInline):
    model = Step
    extra = 0


class ContractPartyInline(TabularInline):
    model = ContractParty
    extra = 0


class SupplementInline(TabularInline):
    model = Supplement
    extra = 0


@admin.register(Contract)
class ContractAdmin(ModelAdmin):
    list_display = ['title', 'no', 'price', 'status', 'manager_accept', 'fund_accept', 'convention_accept', 'committee_accept', 'deputy_accept', 'head_accept', 'drafted', 'draft_accept']
    list_filter = ['manager_accept', 'fund_accept', 'convention_accept', 'committee_accept', 'deputy_accept', 'head_accept', 'drafted', 'draft_accept', 'type', 'genre', 'project__unit', 'agreement']
    inlines = [StepInline, ContractPartyInline, SupplementInline, ContractTaskInline]
    raw_id_fields = ['registrar', 'project']
    search_fields = ['title', 'no']
    readonly_fields = ['no']
    save_on_top = True


class PayTaskInline(TabularInline):
    model = PayTask
    raw_id_fields = ['user']
    extra = 0


@admin.register(Step)
class StepAdmin(ModelAdmin):
    list_display = ['title', 'contract', 'price', 'percent', 'start_date', 'finish_date']
    list_filter = ['contract__project__unit']
    raw_id_fields = ['contract']
    search_fields = ['title', 'contract__title', 'contract__no', 'contract__project__title']

    def get_queryset(self, request):
        return Step.objects.select_related('contract', 'contract__project', 'contract__project__unit')


@admin.register(Pay)
class PayAdmin(ModelAdmin):
    list_display = ['step', 'date', 'bill', 'manager_accept', 'convention_accept', 'fund_accept', 'clerk_accept', 'deputy_accept', 'head_accept', 'finance_accept', 'paid', 'status']
    list_filter = ['step__contract__project__unit', 'manager_accept', 'convention_accept', 'fund_accept', 'clerk_accept', 'deputy_accept', 'head_accept', 'finance_accept', 'paid']
    inlines = [PayTaskInline]
    raw_id_fields = ['registrar', 'step']
    search_fields = ['step__contract__title', 'step__contract__no']
    save_on_top = True


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(ModelAdmin):
    list_display = ['title', 'parent', 'description']
    autocomplete_fields = ['owners']
    search_fields = ['title']


class ArticleAttachmentInline(TabularInline):
    model = ArticleAttachment
    extra = 0


@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    list_display = ['title', 'unit', 'user', 'category', 'is_available']
    list_filter = ['is_available', 'category', 'unit']
    inlines = [ArticleAttachmentInline]
    autocomplete_fields = ['unit', 'user', 'category']
    raw_id_fields = ['step']
    search_fields = ['title', 'contract__title', 'contract__no']
    queryset = Article.objects.select_related('user', 'unit', 'category', 'contract')


@admin.register(ArticlePermit)
class ArticleAttachmentPermitAdmin(ModelAdmin):
    list_display = ['article', 'user', 'accept']
    list_filter = ['article__category', 'accept']
    autocomplete_fields = ['user', 'article']
    queryset = ArticlePermit.objects.select_related('article', 'user')


@admin.register(ArticleChat)
class ArticleChatAdmin(ModelAdmin):
    list_display = ['body', 'article', 'user', 'create_time']
    search_fields = ['body']
    autocomplete_fields = ['user', 'article']
    queryset = ArticleChat.objects.select_related('user', 'article')


@admin.register(ArticleRate)
class ArticleRateAdmin(ModelAdmin):
    list_display = ['article', 'user', 'rate', 'create_time']
    search_fields = ['article__category', 'rate']
    autocomplete_fields = ['user', 'article']
    queryset = ArticleRate.objects.select_related('user', 'article')


@admin.register(ArticleAttachment)
class ArticleAttachmentAdmin(ModelAdmin):
    list_display = ['title', 'author', 'article']
    search_fields = ['title', 'author']

