from django.db import models


class Flats(models.Model):
    link = models.CharField('Ссылка', unique=True, max_length=300)
    reference = models.CharField('Ресурс', max_length=30)
    price = models.IntegerField('Цена', blank=True, null=True)
    title = models.CharField('Название', max_length=1000, blank=True, null=True)
    square = models.IntegerField('Площадь', blank=True, null=True)
    city = models.CharField('Населенный пункт', max_length=30, blank=True, null=True)
    street = models.CharField('Улица(адрес)', max_length=500, blank=True, null=True)
    district = models.CharField('Район', max_length=100, blank=True, null=True)
    microdistrict = models.CharField('Микрорайон', max_length=500, blank=True, null=True)
    rooms_number = models.IntegerField('Количество комнат', blank=True, null=True)
    year = models.IntegerField('Год постройки', blank=True, null=True)
    description = models.CharField('Описание', max_length=3000, blank=True, null=True)
    seller_number = models.CharField('Номер продавца', max_length=30, blank=True, null=True)
    date = models.DateTimeField('Дата объявления', blank=True, null=True)
    is_tg_posted = models.BooleanField('Размещено в ТГ', default=False)
    is_archive = models.BooleanField('Архивное', default=False)

    def __str__(self):
        return self.link

    class Meta:
        verbose_name = "Квартира"
        verbose_name_plural = "Квартиры"
        ordering = ('id',)
        db_table = 'flats'


class Photos(models.Model):
    flat = models.ForeignKey(Flats, db_column='flat', verbose_name='Квартира', related_name='photos', on_delete=models.CASCADE)
    link = models.CharField('Ссылка', unique=True, max_length=1000)
    photo = models.BinaryField('Фото')

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"
        ordering = ('flat', 'id')
        db_table = 'photos'

