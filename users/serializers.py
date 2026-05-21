
from django.conf import settings
from rest_framework import serializers
from .models import PasswordResetOtp, User, Student, Instructor, InstructorLinks
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail 
from django.utils.crypto import get_random_string

class StudentRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(read_only=True)  

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'is_active', 'is_verified', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role='student'
        )
        user.save()
        student= Student.objects.create(user=user)
        return user
    
    
    #############login ################
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user_obj = None 

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required")

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_verified:
            raise serializers.ValidationError("Email is not verified")

        if not user.is_active:
            raise serializers.ValidationError("Account is inactive")

        refresh = RefreshToken.for_user(user)
        attrs['access'] = str(refresh.access_token)
        attrs['refresh'] = str(refresh)
        attrs['user_obj'] = user  
        
        return attrs
    
    ##########student#############
class StudentSerializer(serializers.ModelSerializer):
     email = serializers.CharField(source="user.email", read_only=True)
     first_name = serializers.CharField(source="user.first_name", read_only=True)
     last_name = serializers.CharField(source="user.last_name", read_only=True)
     slug = serializers.CharField(source="user.slug", read_only=True)
     is_verified =serializers.BooleanField(source="user.is_verified",read_only=True)
     image = serializers.ImageField(source="user.image", read_only=True)
     
     class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'slug','is_verified','image']
        
        ####UpdateSerializer for student profile

class StudentUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    image = serializers.ImageField(source="user.image")

    class Meta:
        model = Student
        fields = ['first_name', 'last_name',  'image']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        for attr in ['first_name', 'last_name',  'image']:
            if attr in user_data:
                setattr(user, attr, user_data[attr])
        user.save()

      
        # instance.some_field = validated_data.get('some_field', instance.some_field)
        # instance.save()

        return instance
        
        
        ###################instructor####################
# ================= Instructor Links Serializer =================
class InstructorLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorLinks
        fields = ['slug', 'platformName', 'url']


# class InstructorSerializer(serializers.ModelSerializer):
#      email = serializers.CharField(source="user.email", read_only=True)
#      first_name = serializers.CharField(source="user.first_name", read_only=True)
#      last_name = serializers.CharField(source="user.last_name", read_only=True)
#      slug = serializers.CharField(source="user.slug", read_only=True)
#      image = serializers.ImageField(source="user.image", read_only=True)
#      created_at = serializers.DateField(format="%Y-%m-%d", read_only=True)
        
#      class Meta:
#         model = Instructor
#         fields = ['first_name', 'last_name', 'email', 'slug','bio','image','created_at']
    
    ###==================instructor details============================
        
class InstructorSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    slug = serializers.CharField(source="user.slug", read_only=True)
    image = serializers.ImageField(source="user.image", read_only=True)
    created_at = serializers.DateTimeField(source="user.created_at", format="%Y-%m-%d", read_only=True)
    links = InstructorLinksSerializer(many=True, read_only=True)

    class Meta:
        model = Instructor
        fields = ['first_name', 'last_name', 'email', 'slug', 'bio', 'description', 'image', 'links', 'created_at']
        
        
        ##====================update instructor========================
class InstructorUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    image = serializers.ImageField(source="user.image")
    bio = serializers.CharField()
    description = serializers.CharField()
    links = InstructorLinksSerializer(many=True, read_only=True)

    class Meta:
        model = Instructor
        fields = ['first_name', 'last_name',  'image', 'bio', 'description','links']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.image = user_data.get('image', user.image)
        user.save()

        instance.bio = validated_data.get('bio', instance.bio)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance
    
    
#=====================create instructor========================

class InstructorCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    # validate email
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def create(self, validated_data):
        password = get_random_string(length=8)

        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role='instructor',
            password=password
        )
        user.is_verified = True
        user.save()

        instructor = Instructor.objects.create(user=user)

        send_mail(
            subject="Instructor Account Created",
            message=f"""
Hello {user.first_name},

Your instructor account has been created.

Email: {user.email}
Temporary Password: {password}

Please change your password after login.
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email]
        )

        return instructor
    
    
# ================= Forget Password Serializer =================
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        if not User.is_verified:
            raise serializers.ValidationError("This account is not verified. You cannot reset the password.")
        return value

# ================= Reset Password Serializer =================
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import PasswordResetOtp

User = get_user_model()

class ResetPasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        otp_value = attrs.get("otp")
        new_password = attrs.get("new_password")

        try:
            otp_record = PasswordResetOtp.objects.get(otp=otp_value)
        except PasswordResetOtp.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

        if otp_record.is_expired():
            otp_record.delete()
            raise serializers.ValidationError("OTP has expired.")

        try:
            user = User.objects.get(email=otp_record.email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")

        attrs['user'] = user
        attrs['otp_record'] = otp_record
        return attrs

    def save(self):
        user = self.validated_data['user']
        otp_record = self.validated_data['otp_record']
        new_password = self.validated_data['new_password']

        user.set_password(new_password)
        user.save()
        otp_record.delete()

        return user
    

##change password serializer 
class changePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user= self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value
    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("New password must be at least 8 characters long")
        return value
    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user
    
class AdminProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'slug', 'image', 'created_at']
        
       

    