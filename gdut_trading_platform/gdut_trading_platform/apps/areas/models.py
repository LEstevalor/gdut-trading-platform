from django.db import models


class Area(models.Model):
    """省区划"""
    name = models.CharField(max_length=20, verbose_name='名称')    # 省市区的名称
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True,
                               verbose_name='上级⾏政区划')

    class Meta:
        db_table = 'tb_areas'
        verbose_name = '⾏政区划'
        verbose_name_plural = '⾏政区划'

    def __str__(self):
        return self.name
