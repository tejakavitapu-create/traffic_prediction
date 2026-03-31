from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from admins.models import RegisterUserTable

#------------------------------------------------------------------------------------------------------------
def BasePage(request):
    return render(request, 'base/base.html')

#-------------------------------------------------------------------------------------------------------------


#-------------------------------------------------------------------------------------------------------------
def RegisterUserPage(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        pswd = request.POST['pswd']
        address = request.POST['address']

        if RegisterUserTable.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif RegisterUserTable.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            users = RegisterUserTable.objects.create(
                username=username,
                email=email,
                password=pswd,
                address=address,
            )
            users.save()
            messages.success(request, 'User Registered Successfully.')

        return redirect('register')  
    return render(request,'admins/register.html')

#-------------------------------------------------------------------------------------------------------------

def UserLoginPage(request):
    if request.method =='POST':
        username = request.POST['username']
        pswd = request.POST['password']
        try:
            user = RegisterUserTable.objects.get(username=username, password=pswd)
            if user.is_active:
               request.session['username'] = user.username
               request.session['email'] = user.email
               request.session['address'] = user.address
               return redirect('userhome')
            else:
                messages.error(request, 'Your Account is not Activate, Please Activate and Try again.')
        except RegisterUserTable.DoesNotExist:
            messages.error(request, 'Invalid username or password.') 
    return render(request, 'admins/login.html')

#-------------------------------------------------------------------------------------------------------------

def AdminLoginPage(request):
    if request.method == 'POST':
        usrid = request.POST.get('username')
        pswd = request.POST.get('password')
        print("User ID is = ", usrid)
        if usrid == 'admin' and pswd == 'admin':
            return render(request, 'admins/adminhome.html')
        else:
            messages.success(request, 'Please Check Your Login Details')
    return render(request, 'admins/adminlogin.html')

#----------------------------------------------------------------------------------------------------------------

def ViewUserPage(request):
    users = RegisterUserTable.objects.all()
    return render(request, 'admins/userlist.html',{'users':users})

#---------------------------------------------------------------------------------------------------------------

def UserActivateFunction(request, pk):
    user = get_object_or_404(RegisterUserTable, id=pk)
    user.is_active = True
    user.save()      
    return redirect(ViewUserPage)

# ---------------------------------------------------------------------------------

def UserDeactivateFunction(request, pk):
    user = get_object_or_404(RegisterUserTable, id=pk)
    user.is_active = False
    user.save()      
    return redirect(ViewUserPage)

#------------------------------------------------------------------------------------------

def user_edit(request, pk):
    user = get_object_or_404(RegisterUserTable, pk=pk)
    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.address = request.POST.get('address')
        user.save()
        return redirect(ViewUserPage)  # replace with the name of the view to redirect after saving
    return render(request, 'admins/userlist.html', {'user': user})

from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = RegisterUserTable.objects.get(username=username, password=password)
            if user.is_active:
                return JsonResponse({
                    'status': 'success',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'address': user.address,
                        'role': 'user' if user.username != 'admin' else 'admin'
                    }
                })
            else:
                return JsonResponse({'status': 'error', 'error': 'Account not active'}, status=403)
        except RegisterUserTable.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    return JsonResponse({'error': 'POST required'}, status=405)

@csrf_exempt
def api_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            address = data.get('address', '')

            if RegisterUserTable.objects.filter(username=username).exists():
                return JsonResponse({'status': 'error', 'error': 'Username already exists'}, status=400)
            
            user = RegisterUserTable.objects.create(
                username=username,
                email=email,
                password=password,
                address=address,
                is_active=True # Auto-activate for mobile testing convenience
            )
            return JsonResponse({
                'status': 'success',
                'user': {
                    'username': user.username,
                    'email': user.email
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    return JsonResponse({'error': 'POST required'}, status=405)
