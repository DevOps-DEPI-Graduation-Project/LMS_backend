from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.text import slugify
import uuid
 
# =================== User Manager ===================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

# =================== User ===================
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    image = models.ImageField(upload_to='photo/', null=True, blank=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True,null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    ## for email verification
    otp=models.CharField(max_length=6, blank=True, null=True)
    otp_created_at=models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
            name = f"{self.first_name} {self.last_name}".strip()
            return name if name else self.email

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  
  

    objects = UserManager() 
   

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.first_name)}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
    def __str__(self):
        return self.email

# =================== Student ===================
class Student(models.Model):
    user = models.OneToOneField(User, related_name="student_profile", on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - Student"

# =================== Instructor ===================
class Instructor(models.Model):
    user = models.OneToOneField(User, related_name="instructor_profile", on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - Instructor"
    
    
#==========================instructor links=============================
class InstructorLinks(models.Model):
    instructor=models.ForeignKey(Instructor,related_name="links" ,on_delete=models.CASCADE)
    platformName= models.CharField(max_length=100)
    url=models.URLField()
    slug = models.SlugField(max_length=100, unique=True, blank=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            unique_id = str(uuid.uuid4())[:6]
            self.slug = slugify(f"{self.platformName}-{unique_id}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.instructor} {self.platformName} "

 
class PasswordResetOtp(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 300
    def __str__(self):
        return f"{self.email} - OTP: {self.otp}"
