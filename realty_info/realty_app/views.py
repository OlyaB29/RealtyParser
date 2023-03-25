from django.shortcuts import render
from django.db.models import OuterRef, Subquery
from . import django_sentry_logger
import logging
import datetime
from .models import Flats, Photos
from .forms import FlatForm
import newrelic.agent

newrelic.agent.initialize('E:\Olya Work\\Users\oabor\PycharmProjects\RealtyParser\\newrelic.ini')

logger = logging.getLogger('views')
logger.setLevel(logging.INFO)


def info(request):
    def newrelic_info(request):
        error = ''
        if request.method == 'POST':
            form = FlatForm(request.POST)
            if form.is_valid():
                if form.cleaned_data['city']:
                    city = form.cleaned_data['city'].title()
                    if city.isdigit():
                        logger.error('The city is entered in numbers')
                else:
                    city = ''
                if form.cleaned_data['district']:
                    district = form.cleaned_data['district'].title()
                else:
                    district = ''
                if form.cleaned_data['rooms_number']:
                    rooms_number = [form.cleaned_data['rooms_number']]
                else:
                    rooms_number = [1, 2, 3, 4, 5]

                flats = Flats.objects.filter(date__gte=datetime.datetime.today() - datetime.timedelta(days=5),
                                         is_archive=False,
                                         city__contains=city, district__contains=district,
                                         rooms_number__in=rooms_number).order_by('-date')

                photos = Photos.objects.filter(flat=OuterRef("pk"))
                flats = flats.annotate(first_photo=Subquery(photos.values('link')[:1]),
                                   second_photo=Subquery(photos.values('link')[1:2]),
                                   third_photo=Subquery(photos.values('link')[2:3]))
                logger.info(f'Number of selected flats: {len(flats)}')
                return render(request, 'realty_app/selected_flats.html', {'flats': flats})
            else:
                error = 'Форма заполнена неверно'
                logger.error('Form is not valid')

        form = FlatForm()
        context = {
            'form': form,
            'error': error
        }

        return render(request, 'realty_app/info.html', context)

    def execute_task(application, task_name):
        with newrelic.agent.BackgroundTask(application, name=task_name, group='Task'):
            global rend
            rend=newrelic_info(request)

    execute_task(newrelic.agent.register_application(timeout=0.2), "django_info")

    return rend

