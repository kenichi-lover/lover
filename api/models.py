from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class UserInfo(AbstractUser):
    token = models.CharField(verbose_name='TOKEN', max_length=64, null=True, blank=True, db_index=True)
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

class Blog(models.Model):

    category_choices = ((1,'云计算'),(2,'python全栈'),(3,'go开发'))
    category = models.IntegerField(verbose_name='分类',choices=category_choices)
    image = models.CharField(verbose_name='封面',max_length=255)
    title = models.CharField(verbose_name='标题',max_length=32)
    summary = models.CharField(verbose_name='简介',max_length=256)
    text = models.TextField(verbose_name='博文')
    ctime = models.DateTimeField(verbose_name='创建时间',auto_now_add=True)
    creator = models.ForeignKey(verbose_name='创建者',to=UserInfo,on_delete=models.CASCADE)

    comment_count = models.PositiveIntegerField(verbose_name='评论数',default=0)
    favor_count = models.PositiveIntegerField(verbose_name='赞数',default=0)


class Comment(models.Model):
    '''评论表'''
    blog = models.ForeignKey(Blog,on_delete=models.CASCADE,verbose_name='博客')
    user = models.ForeignKey(UserInfo,on_delete=models.CASCADE,verbose_name='用户')
    content = models.CharField(verbose_name='内容',max_length=255)
    create_datetime = models.DateTimeField(verbose_name='创建时间',auto_now_add=True)

class Favor(models.Model):
    '''赞'''
    blog = models.ForeignKey(Blog,on_delete=models.CASCADE,verbose_name='博客')
    user = models.ForeignKey(UserInfo,on_delete=models.CASCADE,verbose_name='用户')
    create_datetime = models.DateTimeField(verbose_name='创建时间',auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['blog','user'],name='unique_f')
        ]
