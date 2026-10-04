from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db.models import BooleanField, CharField, EmailField


class UserManager(BaseUserManager):
    
    def create_user(
        self, 
        email:str, 
        first_name:str, 
        last_name:str, 
        password:str, 
        **extra_fields
    ) -> "User":
        """Create custom user."""
        
        if not email:
            raise ValidationError(("email is required"), code="empty field")
        if not first_name:
            raise ValidationError(("first_name is required"), code="empty first name field")
        if not last_name:
            raise ValidationError(("last name is required"), code="empty last name field")
        
        user: User = self.model( 
            email = self.normalize_email(email), 
            first_name=first_name, 
            last_name=last_name
            **extra_fields,
        )
            
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, 
        email:str, 
        first_name:str, 
        last_name:str, 
        password:str, 
        **extra_fields
    ) -> "User":
        """Create super user. Used in manage.py createsuperuser"""
        if not email:
            raise ValidationError(("email is required"), code="empty field")
        if not first_name:
            raise ValidationError(("first_name is required"), code="empty first name field")
        if not last_name:
            raise ValidationError(("last name is required"), code="empty last name field")

        user: User = self.model( 
            email = self.normalize_email(email), 
            first_name=first_name, 
            last_name=last_name,
            is_staff=True, 
            is_superuser=True,
            **extra_fields
        )
            

        user.set_password(password)
        user.save(using=self._db)
        return user
    


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model, extending AbstractBaseUser and PermissionsMixin.
    """
    
    FIRST_NAME_MAX_LENGTH = 50
    LAST_NAME_MAX_LENGTH = 50 

    email = EmailField(
        unique=True
    )
    first_name = CharField(
        max_length=FIRST_NAME_MAX_LENGTH
    )
    last_name = CharField(
        max_length=LAST_NAME_MAX_LENGTH
    ) 
    is_active = BooleanField(
        default=True
    )
    is_staff = BooleanField(
        default=False
    )
    
    REQUIRED_FIELDS = ("first_name", "last_name")
    USERNAME_FIELD = "email"

    objects = UserManager()