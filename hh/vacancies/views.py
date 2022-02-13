from collections import Counter

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from el_pagination.views import AjaxListView

from .forms import VacancyForm
from .models import Vacancy
from accounts.models import UserStatus, Employer
from recruiting.models import Response


class VacancyList(LoginRequiredMixin, AjaxListView):
    model = Vacancy
    page_template = 'vacancies/snippets/list/cards.html'
    TOTAL_K = _('Все')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(VacancyList, self).get_context_data(object_list=object_list, **kwargs)
        context.update({'title': 'Вакансии'})
        vacancies = self.filter(context, object_list)
        # Get employers and link them to vacancies
        context['employers_vac_list'] = []
        for vacancy in vacancies:
            response = None
            fav = False
            if self.request.user.status == UserStatus.JOBSEEKER and \
                    self.request.user in vacancy.favourites.all():
                fav = True
            if self.request.user.status == UserStatus.JOBSEEKER and \
                    Response.objects.filter(vacancy=vacancy, resume__user=self.request.user).exists():
                response = Response.objects.get(vacancy=vacancy, resume__user=self.request.user)
            context['employers_vac_list'].append(
                [Employer.objects.get(user=vacancy.employer), vacancy, response, fav])

        return context

    def get_queryset(self):
        queryset = super().get_queryset().order_by('created_at')
        if self.request.user.status == UserStatus.EMPLOYER:
            queryset = queryset.filter(employer=self.request.user).select_related('employer')
        if self.request.user.status == UserStatus.JOBSEEKER:
            queryset = queryset.filter(status=Vacancy.PUBLISHED)
        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.is_ajax() and 'page' not in self.request.GET:
            result = render_to_string(self.page_template, context=context, request=self.request)
            return JsonResponse({'result': result})
        return super(VacancyList, self).render_to_response(context, **response_kwargs)

    def filter(self, context, object_list):
        city_id = 0
        # Check if search by city was invoked
        if 'city_id' in self.request.GET:
            city_id = int(self.request.GET['city_id'])
            vacancies_city, employers = filter_by_city(object_list, city_id)
        else:
            vacancies_city, employers = filter_by_city(object_list, 0)
            context['vacancy_cities'] = get_vacancy_cities(vacancies_city)
            context['vacancy_cities'].insert(0, (self.TOTAL_K, len(object_list)))

        # Check if normal search was invoked
        if 'search' in self.request.GET:
            text = self.request.GET['search']
            vacancies = list(vacancies_city.filter(
                Q(title__contains=text) |
                Q(salary__contains=text) |
                Q(hashtags__contains=text)
            ).order_by('created_at'))
            if city_id:
                employers = [empl.user for empl in
                             employers.filter(
                                 Q(name__contains=text) |
                                 Q(description__contains=text),
                                 city__id=city_id
                             ).select_related('user')]
            else:
                employers = [empl.user for empl in
                             employers.filter(
                                 Q(name__contains=text) |
                                 Q(description__contains=text)
                             ).select_related('user')]
            employer_vacancies = list(object_list.filter(employer__in=employers).order_by('created_at'))
            vacancies.extend(employer_vacancies)
            vacancies = list(dict.fromkeys(vacancies))
        else:
            vacancies = vacancies_city

        return vacancies


class VacancyDetail(LoginRequiredMixin, DetailView):
    model = Vacancy
    extra_context = {'title': 'Детали Вакансии'}


class VacancyCreate(LoginRequiredMixin, CreateView):
    model = Vacancy
    form_class = VacancyForm
    extra_context = {'title': 'Создание Вакансии'}
    success_url = reverse_lazy('vacancies:vacancy_list')

    def form_valid(self, form):
        form.instance.employer_id = self.kwargs.get('pk')
        return super(VacancyCreate, self).form_valid(form)


class VacancyUpdate(LoginRequiredMixin, UpdateView):
    model = Vacancy
    form_class = VacancyForm
    extra_context = {'title': 'Изменение Вакансии'}
    success_url = reverse_lazy('vacancies:vacancy_list')


class VacancyDelete(LoginRequiredMixin, DeleteView):
    model = Vacancy
    extra_context = {'title': 'Удаление Вакансии'}
    success_url = reverse_lazy('vacancies:vacancy_list')


def get_vacancy_cities(vacancies):
    employer_cities = [Employer.objects.get(user=vac.employer).city for vac in vacancies]
    cities = sorted(Counter(employer_cities).items(), key=lambda x: x[1], reverse=True)
    return cities


def filter_by_city(vacancies, city_id):
    # Get all vacancy employers accounts
    empl_acc_all = list(dict.fromkeys([vac.employer for vac in vacancies]))
    # Get relevant employers
    if city_id != 0:
        employers = Employer.objects.filter(user__in=empl_acc_all, city__id=city_id).select_related('user')
        vacancies = Vacancy.objects.filter(employer__in=[empl.user for empl in employers]).order_by('created_at').select_related('employer')
    else:
        employers = Employer.objects.filter(user__in=empl_acc_all).select_related('user')
    return vacancies, employers
