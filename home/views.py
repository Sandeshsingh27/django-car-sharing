from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.db.models import F
from .models import *
from car_sharing import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from .tokens import generate_token
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from datetime import datetime
import math


def home(request):
    return render(request, "homepage.html")

def pickRide(request):
    return render(request, "pickRide.html")

def yourRide(request, user):
    rides=Post.objects.filter(user=user)
    print(rides)
    context={"rides":rides}
    return render(request, "yourRides.html", context)

def updateRide(request, id):
    context={}
    if request.method=='POST':
        source = request.POST['source']
        destination = request.POST['destination']
        vacant_seats = request.POST['vacant_seats']
        date_of_trip = request.POST['date_of_trip']
        time_of_trip = request.POST['time_of_trip']
        price = request.POST['price']
        car_name = request.POST.get('car_name')
        ride=Post.objects.get(id=id)
        ride.source=source
        ride.destination=destination
        ride.date_of_trip=date_of_trip
        ride.time_of_trip=time_of_trip
        ride.vacant_seats=vacant_seats
        ride.car_name=car_name
        ride.price=price

        ride.save()
        print(request.user.id)

        messages.success(request, "Your Ride has been updated")

        # Here we are concatinating logged in user_id with url
        user_id=request.user.id
        url = '/yourRide/{}'.format(user_id)  # yourRide/{{logged_in_user_id}}
        return redirect(url)
    else:
        ride=Post.objects.get(id=id)
        context.update({"ride":ride})
    return render(request, "editRide.html", context)

def deleteRide(request, id):
    ride=Post.objects.get(id=id)
    
    if ride:
        ride.delete()

        messages.error(request, "Your Ride has been deleted")

        # Here we are concatinating logged in user_id with url
        user_id=request.user.id
        url = '/yourRide/{}'.format(user_id)  # yourRide/{{logged_in_user_id}}
        return redirect(url)
    else:
        messages.error(request, "Some Problem Occured! Your Ride cannot be deleted. Please try again!")
        return render(request, 'homepage.html')


def contact(request):
    if request.method=='POST':
        name= request.POST.get('name')
        email= request.POST.get('email')
        phone= request.POST.get('phone')
        desc= request.POST.get('desc')

        instance = Contact(name=name, email=email, phone=phone, desc=desc)
        instance.save()
        messages.success(request, "Your query has been saved")
    return render(request, "contact.html")


def PubRide(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            user=request.user
            source = request.POST['source']
            destination = request.POST['destination']
            vacant_seats = request.POST['vacant_seats']
            date_of_trip = request.POST['date_of_trip']
            time_of_trip = request.POST['time_of_trip']
            price = request.POST['price']
            car_name = request.POST.get('car_name')

            post1 = Post(
                user=user,source=source, destination=destination, vacant_seats=vacant_seats, date_of_trip=date_of_trip, time_of_trip=time_of_trip, price=price, car_name=car_name)

            post1.save()

            messages.success(request, "Your ride has been successfully posted")
            return render(request, "PubRide.html", {'username': request.user.username})
        else:
            messages.error(request, "Please login to post a ride.")
            return render(request, "logIn.html")
    return render(request, "PubRide.html")

def pagination(page, rides):
    # PAGINATION LOGIC STARTS
    # designing pagination logic
    no_of_posts=2
    # page= request.GET.get('page') # fetching value from url

    # By default, request.GET.get('page') returns string and if there is no page then return None
    # so if there is no page, make page = 1 otherwise convert ot integer
    if page is None:
        page = 1
    else:
        page = int(page)

    
    # counting all blogs in the databases to perform pagination logic
    length = len(rides)
    # here we are using python slicing function
    # below line just used to show how many blogs can be rendered on blog page and from where to where (ie, if page = 1, then blogs from index 0 to 2 will be displayed)
    rides = rides[(page-1)*no_of_posts: page*no_of_posts]

    # if page is greater than 1 then prev will be decremented by page-1 else make it None
    if page > 1:
        prev=page-1
    else:
        prev=None

    # Similarly, if page is less than ceiling value of required number of pages then nxt will be incremented by page+1 else make it None
    if page<math.ceil(length/no_of_posts):
        nxt=page+1
    else:
        nxt=None

    return rides, prev, nxt
    
    # PAGINATION LOGIC ENDS


def rides(request):
    if request.method == "POST":
        leave = request.POST.get('leave')
        arrive = request.POST.get('arrive')
        date = request.POST.get('date')
        # number_of_passengers so that we can pass it through url to use it on ride.html
        number = request.POST.get('number')
        lookup = (Q(source__icontains=leave) &
                  Q(destination__icontains=arrive))
        if leave != None and arrive != None and date != None and number != None:
            rides = Post.objects.filter(Q(lookup))

            # if vacant_seats is less than the user demand then we are not showing that particular ride and if date and time of trip is less than todays date and time
            for ride in rides:
                if ride.vacant_seats < int(number) or (ride.date_of_trip < datetime.now().date() and ride.time_of_trip < datetime.now().time()):
                    rides=rides.exclude(id = ride.id)
            
            # these blocks are for pagination 
            page= request.GET.get('page')
            rides, prev, nxt = pagination(page, rides)

            context={'rides': rides,'number':number, 'prev':prev, 'nxt':nxt}

            return render(request, "rides.html", context)
    else:
        rides=Post.objects.all()
        # if date and time of trip is less than todays date and time then we are not showing in all rides 
        for ride in rides:
            if ride.date_of_trip < datetime.now().date() and ride.time_of_trip < datetime.now().time():
                rides=rides.exclude(id = ride.id)

        # these blocks are for pagination 
        page= request.GET.get('page')
        rides, prev, nxt = pagination(page, rides)

        context={'rides': rides, 'prev':prev, 'nxt':nxt}

        return render(request, "allRides.html", context)


def decrease_counter(request, pk):
    if request.method == "POST":
        ride = Post.objects.get(id=pk)
        # getting number_of_passenger through url get method
        number=request.GET.get('number')
        ride.vacant_seats = F('vacant_seats') - number
        ride.save()
        return render(request, "success.html")


def success(request):
    return render(request, "success.html")


def register(request):
    if request.method == "POST":
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        if User.objects.filter(username=username):
            messages.error(
                request, "Username already exist! Please try some other username.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return render(request, "register.html")

        if len(username) > 20:
            messages.error(request, "Username must be under 20 charcters!!")
            return render(request, "register.html")

        if pass1 != pass2:
            messages.error(request, "Passwords didn't matched!!")
            return render(request, "register.html")

        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!!")
            return render(request, "register.html")

        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = first_name
        myuser.last_name = last_name
        myuser.is_active = False
        myuser.save()

        messages.success(
            request, "Your account has been successfully created. Please confirm your email ID by clicking on the confirmation link sent.")

        # Welcome Email
        subject = "Welcome to Car Sharing Service!!"
        message = "Hello " + myuser.first_name + "!! \n" + \
            "Welcome to Car Sharing Service!! \nThank you for visiting our website.\n We have also sent you a confirmation email, please confirm your email address. \n\nThanking You\n Ayush Bajpai"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        # Email Address Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your Email @ Car Sharing Service!!"
        message2 = render_to_string('email_confirmation.html', {

            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser),
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()

        return render(request, "logIn.html")

    return render(request, "register.html")


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        # user.profile.signup_confirmation = True
        myuser.save()
        login(request, myuser)
        messages.success(request, "Your Account has been activated!!")
        # context = {'uidb64': uidb64, 'token': token}
        return render(request, "logIn.html")
    else:
        return render(request, 'activation_failed.html')


def logIn(request):
    if request.method == "POST":
        username = request.POST['username']
        pass1 = request.POST['pass1']
        user = authenticate(username=username, password=pass1)

        if user is not None:
            login(request, user)
            return render(request, "homepage.html", {'username': username})

        else:
            messages.error(request, "Bad credential!")
            return render(request, "homepage.html")

    return render(request, "logIn.html")


def logOut(request):
    logout(request)
    messages.success(request, "Logged out successfully !")
    return render(request, "homepage.html")
