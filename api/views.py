from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.versioning import QueryParameterVersioning
from rest_framework.parsers import JSONParser,FormParser
from rest_framework.negotiation import DefaultContentNegotiation
from django.contrib.auth import authenticate

from api.models import Blog, Comment,Favor
from api.serializers import BlogSerializer, CommentSerializer, RegisterSerializer, LoginSerializer, FavorSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class HomeView(APIView):
    # 所有解析器,可以不写，默认有
    parser_class = (JSONParser,FormParser)
    # 根据请求，匹配对应的解析器
    content_negotiation_class = DefaultContentNegotiation

    versioning_class = QueryParameterVersioning
    def get(self, request):
        print(request.version)

        return Response({'message': 'Hello, World!'})

    def post(self, request, *args, **kwargs):
        # 当调用request.data时就会触发解析的动作。
        print(request.data,type(request.data))
        return Response({'message': 'Hello, World!'})

class BlogView(APIView):
    authentication_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        # 读取数据库的博客信息
        queryset = Blog.objects.all().order_by('-id')

        # 序列化
        serializer = BlogSerializer(queryset, many=True)

        # 返回
        return Response(serializer.data)

    def post(self, request):
        # 在实例化 BlogSerializer 时，我们传递了 context={'request': request}。
        # 这使得 Serializer 能够访问 request 对象，从而获取当前登录的用户 (request.user)。
        serializer = BlogSerializer(data=request.data,context={'request': request})

        if serializer.is_valid():
            # 这会将当前登录的用户对象作为 creator 参数传递给 Serializer 的 create() 方法。
            serializer.save(creator=request.user)  # 保存时设置 creator 为当前用户

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BlogDetailView(APIView):
    def get(self, request, *args, **kwargs):
        # 获取ID
        pk = kwargs.get('pk')
        # 根据ID获取对象
        instance = Blog.objects.filter(pk=pk).first()
        if not instance:
            return Response({'message': 'Blog not found'})
        # 序列化
        serializer = BlogDetailView(instance=instance, many=False)
        # 返回
        return Response(serializer.data)

class CommentView(APIView):
    def get(self, request, blog_id):
        queryset = Comment.objects.filter(blog_id=blog_id)
        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, blog_id):
        if not request.user.is_authenticated:
            return Response({'message': 'You are not authenticated'})
        blog = Blog.objects.get(pk=blog_id)
        if not blog:
            return Response({'message': 'Blog not found'})

        serializer = CommentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'message': serializer.errors})
        serializer.save(blog=blog, user=request.user)
        return Response(serializer.data)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # 使用 RefreshToken.for_user(user) 为该用户创建一个 RefreshToken 对象。
            refresh = RefreshToken.for_user(user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            },
            status=status.HTTP_200_OK
            )

        return Response(serializer.errors)

class FavorView(APIView):
    # 务必使用 IsAuthenticated 权限类来确保只有登录用户才能执行点赞操作
    authentication_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FavorSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            blog_id = serializer.validated_data['blog_id'] # 从验证后的数据中获取 blog_id
            try:
                blog = Blog.objects.get(pk=blog_id)
            except Blog.DoesNotExist:
                return Response({'error': '指定的 BLOG 不存在。'}, status=status.HTTP_400_BAD_REQUEST)
            # 检查当前用户是否已经给该 BLOG 点过赞
            if Favor.objects.filter(user=request.user, blog=blog).exists():
                return Response({'error': '您已经给该 BLOG 点过赞了。'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer.save(user=request.user, blog=blog)  # 保存点赞信息
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)


