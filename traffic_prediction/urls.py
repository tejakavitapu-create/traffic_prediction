from django.contrib import admin
from django.urls import path
from admins import views as AdminViews
from users import views as UserViews
try:
    from Utility.train_model import training, train_vehicles_model
except ImportError:
    training = train_vehicles_model = None

try:
    from Utility.predict import predict_vehicles
except ImportError:
    predict_vehicles = None

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', AdminViews.BasePage, name='base'),

    path('register', AdminViews.RegisterUserPage, name='register'),
    path('login', AdminViews.UserLoginPage, name='login'),
    path('adminlogin', AdminViews.AdminLoginPage, name='adminlogin'),
    path('api/login', AdminViews.api_login, name='api_login'),
    path('api/register', AdminViews.api_register, name='api_register'),

    path('userlist', AdminViews.ViewUserPage, name='userlist'),
    path('useravtivate/<int:pk>', AdminViews.UserActivateFunction, name='useractivate' ),
    path('userdeavtivate/<int:pk>', AdminViews.UserDeactivateFunction, name='userdeavtivate' ),
    path('user_edit/<int:pk>', AdminViews.user_edit, name='user_edit'),

    path('userhome', UserViews.UserHomePage, name='userhome'),
    path('task1', UserViews.Task1, name='task1'),
    path('task2', UserViews.Task2, name='task2'),
    path('task3', UserViews.Task3, name='task3'),
    path('trafficsense', UserViews.trafficsense, name='trafficsense'),
    path('api/autocomplete', UserViews.autocomplete, name='autocomplete'),
    path('api/traffic', UserViews.traffic, name='traffic'),
    path('api/model-performance', UserViews.model_performance_api, name='model_performance_api'),

    path('training', training, name='training') if training else path('training', AdminViews.BasePage, name='training'),
    path('model', train_vehicles_model, name='model') if train_vehicles_model else path('model', AdminViews.BasePage, name='model'),
    path('predict_vehicles', predict_vehicles, name='predict_vehicles') if predict_vehicles else path('predict_vehicles', AdminViews.BasePage, name='predict_vehicles'),
]
