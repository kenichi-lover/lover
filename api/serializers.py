from rest_framework import serializers
from django.contrib.auth import authenticate
from api.models import Blog, Comment, UserInfo,Favor


class BlogSerializer(serializers.ModelSerializer):
    # 序列化时显示分类的文本表示
    category = serializers.CharField(source='get_category_display',read_only=True)

    # 反序列化时接收分类的整数值
    # write_only=True 表示这个字段仅用于写入操作（创建/更新），不会在序列化输出中显示
    category_value = serializers.IntegerField(write_only=True, required=True)

    ctime = serializers.DateTimeField(format='%Y-%m-%d',read_only=True)

    # 如果 creator 应该始终是当前登录用户，建议在后端处理并在 Serializer 中将其设置为 read_only=True。
    # creator 字段通常在创建时由后端自动设置，可以考虑在 create 方法中处理
    # 或者如果前端需要传递 creator 的 ID，则保持 PrimaryKeyRelatedField
    creator = serializers.PrimaryKeyRelatedField(read_only=True)

    comment_count = serializers.IntegerField(read_only=True)
    favor_count = serializers.IntegerField(read_only=True)

    class Meta: # 这是一个内部类，用于配置 ModelSerializer 的行为
        model = Blog
        fields = ['id','category', 'title', 'creator','image','summary',
                  'ctime','comment_count','favor_count','text']

        read_only_fields = ['id', 'creator', 'ctime', 'comment_count', 'favor_count', 'text']


    def create(self, validated_data):
        validated_data['category'] = validated_data.pop('category_value')
        creator = self.context['request'].user  # 从 context 中获取 user
        blog = Blog.objects.create(creator=creator, **validated_data)
        return blog

    def update(self, instance, validated_data):
        if 'category_value' in validated_data:
            validated_data['category'] = validated_data.pop('category_value')
        return super().update(instance, validated_data)

class BlogDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='get_category_display')
    ctime = serializers.DateTimeField(format='%Y-%m-%d')
    creator = BlogSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    class Meta:
        model = Blog
        fields = '__all__'



class CommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')
    class Meta:
        model = Comment
        fields = ['id','user','content']
        extra_kwargs = {
            'id': {'read_only': True},
            'user': {'read_only': True},
        }

class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = UserInfo
        fields = ['id','username','password','confirm_password']
        extra_kwargs = {'password': {'write_only': True},
                        'id':{'read_only': True}}
    # self 是序列化器实例本身。
    # data 是一个包含经过字段类型验证后的输入数据的字典。
    def validate(self, data): # 这是一个自定义的验证方法。DRF 会在反序列化数据之后，但在保存模型实例之前调用这个方法
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    # 这是一个自定义的创建模型实例的方法。当序列化器的 is_valid() 方法验证通过后，
    # 并且调用了 save() 方法时，这个 create() 方法会被调用
    def create(self, validated_data):
        # 从 validated_data 中移除 confirm_password，因为它不是 UserInfo 模型的字段
        validated_data.pop('confirm_password')
        # 直接使用 validated_data 创建用户
        user = UserInfo.objects.create(username=validated_data['username'])
        # 使用 set_password() 哈希密码
        user.set_password(validated_data['password'])
        user.save()
        return user

'''self 是序列化器实例本身; validated_data 是一个包含已经通过所有验证的输入数据的字典。'''

'''validated_data.pop('confirm_password'): 由于 confirm_password 只是用于密码确认，
它不是 UserInfo 模型中的字段，所以在创建模型实例之前需要将其从 validated_data 中移除，
否则在创建 UserInfo 对象时会因为包含未知的字段而报错。'''

# 注意这里继承的是 serializers.Serializer 而不是 ModelSerializer，更适合登录
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True,required=True)


    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError("必须提供用户名和密码")
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError('用户名或密码错误')

        data['user'] = user  # 将验证通过的用户添加到 validated_data 中

        return data

class FavorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favor
        fields = ['blog']
