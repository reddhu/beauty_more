from django.db import models


class Areas(models.Model):
    name = models.CharField(max_length=20, verbose_name='名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='上级行政区')

    class Meta:
        db_table = 'tb_areas'
        verbose_name = '行政区'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
