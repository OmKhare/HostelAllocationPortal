from django.shortcuts import render, redirect
from .forms import *
from django.http import HttpResponse, Http404
from MainSite.models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import datetime,calendar
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.contrib import messages

def home(request):
    return render(request, 'home.html')

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(
                request,
                username=cd['username'],
                password=cd['password'])
            if user is not None:
                if user.is_warden:
                    return HttpResponse('Invalid Login')
                if user.is_active:
                    login(request, user)
                    return redirect('../student_profile/')
                else:
                    return HttpResponse('Disabled account')
            else:
                #messages.warning(request,'Incorrect User Credentials')
                form = LoginForm()
                return render(request, 'login.html', {'form':form, 'messages':{'Incorrect User Credentials'}})
    else:
        if (request.user.is_authenticated):
            logout(request)
            form = LoginForm()
            return render(request, 'login.html', {'form': form})
        else:
            form = LoginForm()
            return render(request, 'login.html', {'form': form})


def warden_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(
                request,
                username=cd['username'],
                password=cd['password'])
            print(cd['username'],cd['password'])
            print(user)
            if user is not None:
                if not user.is_warden:
                    return HttpResponse('Invalid Login')
                elif user.is_active:
                    login(request, user)

                    students = Student.objects.all()
                    room_list = Room.objects.all()
                    hostel = Hostel.objects.get(name=user.warden.hostel)
                    print(hostel)
                    all_verified = True
                    for student in students:
                        if student.documnets_aproved == False:
                            all_verified = False
                            break
                    if all_verified == True and hostel.alloted == False:
                        final_list = []
                        hostel.alloted = True
                        hostel.save()
                        for student in students:
                            student_list = []
                            list_pref = []
                            list_pref.append(student.pref1)
                            list_pref.append(student.pref2)
                            list_pref.append(student.pref3)
                            list_pref.append(student.pref4)
                            list_pref.append(student.pref5)
                            student_list.append(list_pref)
                            student_list.append(student.current_cgpa)
                            student_list.append(student.enrollment_no)
                            final_list.append(student_list)
                        
                        def func(e):
                            return e[1]

                        final_list.sort(reverse=True, key=func)
                        alloted = {}
                        for i in final_list:
                            for j in i[0]:
                                print(j)
                                room = Room.objects.get(Number = j)
                                if room.vacant == True:
                                    room.vacant = False
                                    room.save()
                                    alloted[i[2]] = j
                                    break
                                else:
                                    alloted[i[2]] = 'NA'  

                        print(alloted)
                        for key in alloted.keys():
                            roomno = alloted[key]
                            enrol = key
                            room = Room.objects.get(Number = roomno)
                            student = Student.objects.get(enrollment_no = enrol)
                            room.student = student
                            room.save()
                            student.room_allotted = True
                            student.room = room
                            student.save()

                    context = {'rooms': room_list}
                    return render(request, 'warden.html', context)
                else:
                    messages.error(request,'Disabled account')
                    return render(request, 'login.html', {'form':form, 'messages':{'Incorrect User Credentials'}})
            else:
                #messages.error(request,'Incorrect User Credentials')
                return render(request, 'login.html', {'form':form, 'messages':{'Incorrect User Credentials'}})
    else:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

@login_required
def warden_profile(request):
    user = request.user
    if user is not None:
        if not user.is_warden:
            return HttpResponse('Invalid Login')
        elif user.is_active:
            login(request, user)
            room_list = request.user.warden.hostel.room_set.all().order_by('Number')
            context = {'rooms': room_list}
            return render(request, 'warden.html', context)
        else:
            return HttpResponse('Disabled account')
    else:
        return HttpResponse('Invalid Login')


@login_required
def student_profile(request):
    user = request.user
    if user is not None:
        if user.is_warden:
            return HttpResponse('Invalid Login')
        if user.is_active:
            login(request, user)
            student = request.user.student
            leaves = Leave.objects.filter(student=request.user.student)
            return render(request, 'profile.html', {'student': student, 'leaves': leaves})
        else:
            return HttpResponse('Disabled account')
    else:
        return HttpResponse('Invalid Login')

@login_required
def upload(request):
    user = request.user
    if user is not None:
        if user.is_warden:
            return HttpResponse('Invalid Login')
        elif user.is_active:
            if request.method == 'POST':
                form = UploadForm(request.POST)
                if form.is_valid():
                    student = user.student
                    cd = form.cleaned_data
                    student.aadharCard = cd['aadharCard']
                    student.photoId = cd['photoId']
                    student.feeReciept = cd['feeReciept']
                    student.documnets_uploaded = True
                    student.save()
                    messages.error(request,'Data Saved Successfully!')
                    return redirect('../student_profile/')
            else:
                student = request.user.student
                if student.documnets_uploaded == False:
                    form = UploadForm()
                    return render(request, 'upload.html', {'form': form})
                else:
                    messages.error(request,'Data already saved!')
                    return redirect('../student_profile/')
        else:
            return HttpResponse('Disabled account')
    else:
        return HttpResponse('Invalid Login')



@login_required
def edit(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, instance=request.user.student)
        if form.is_valid():
            form.save()
            student = request.user.student
            leaves = Leave.objects.filter(student=request.user.student)
            return render(request, 'profile.html', {'student': student, 'leaves': leaves})
        else:
            form = RegistrationForm()
            return render(request, 'edit.html', {'form': form})
    else:
        form = RegistrationForm(instance=request.user.student)
        return render(request, 'edit.html', {'form': form})


@login_required
def select(request):
    if request.method == 'POST':
        form = SelectionFormFloor(request.POST)
        if form.is_valid():
            user = request.user
            if user.is_active:
                cd = form.cleaned_data
                student = user.student
                student.pref1 = str(cd['preference1'])
                student.pref2 = str(cd['preference2'])
                student.pref3 = str(cd['preference3'])
                student.pref4 = str(cd['preference4'])
                student.pref5 = str(cd['preference5'])
                student.prefRec = True
                student.save()
                messages.error(request,'Data Saved Successfully!')
                return redirect('student_profile')
            else:
                form = LoginForm()
                return render(request, 'login.html', {'form': form})
    else:
        if not request.user.student.no_dues:
            return HttpResponse('You have dues. Please contact your Hostel Caretaker or Warden')
        if request.user.student.documnets_uploaded == False:
            messages.error(request,'Please upload the documnets first!')
            return redirect('student_profile')
        if request.user.student.documnets_aproved == False:
            messages.error(request,'Documnets not verified yet!')
            return redirect('student_profile')
        form = SelectionFormFloor()
        students = Student.objects.all()
        dict = {}
        rooms = Room.objects.all()
        for i in rooms:
            dict[i.Number] = []
        pref = {}
        for i in rooms:
            pref[i.Number] = 0
        for i in students:
            dict[i.pref1].append(i.current_cgpa)
            dict[i.pref2].append(i.current_cgpa)
            dict[i.pref3].append(i.current_cgpa)
            dict[i.pref4].append(i.current_cgpa)
            dict[i.pref5].append(i.current_cgpa)

        user = request.user
        student = user.student
        for i in dict:
            for j in dict[i]:
                if(j>student.current_cgpa):
                    pref[i] += 1
        return render(request, 'hostel.html', {'form': form, 'pref': pref})


def repair(request):
    if request.method == 'POST':
        form = RepairForm(request.POST)
        if form.is_valid() & request.user.student.room_allotted:

            rep = form.cleaned_data['repair']
            room = request.user.student.room
            room.repair = rep
            room.save()
            return HttpResponse('<h3>Complaint Registered</h3> <br> <a href = \'../../student_profile\''
                                ' style = "text-align: center; color: Red ;"> Go Back to Profile </a>')
        elif not request.user.student.room_allotted:
            return HttpResponse('<h3>First Select a Room </h3> <br> <a href = \'../select\''
                                ' style = "text-align: center; color: Red ;"> SELECT ROOM </a> ')

        else:
            form = RepairForm()
            room = request.user.student.room
            return render(request, 'repair_form.html', {'form': form, 'room': room})
    else:
        if not request.user.student.room_allotted:
            messages.error(request,'Allocate a Room First!')
            return redirect('student_profile')
        else:
            form = RepairForm()
            room = request.user.student.room
            return render(request, 'repair_form.html', {'form': form,'room': room})

@login_required
def warden_dues(request):
    user = request.user
    if user is not None:
        if not user.is_warden:
            return HttpResponse('Invalid Login')
        else:
            students = Student.objects.all()
            return render(request, 'dues.html', {'students': students})
    else:
        return HttpResponse('Invalid Login')

@login_required
def document_verification(request):
    if request.method == 'POST':
        user = request.user
        if user is not None:
            if not user.is_warden:
                return HttpResponse('Invalid Login')
            else:
                print(request.POST)
                dictionary = request.POST.dict()
                del dictionary['csrfmiddlewaretoken']
                students = Student.objects.all()
                print(students)
                for key in dictionary.keys():
                    print(key)
                    student = Student.objects.get(enrollment_no = key)
                    if student != None:
                        student.documnets_aproved = True
                        student.save()
                room_list = request.user.warden.hostel.room_set.all().order_by('Number')
                context = {'rooms': room_list}
                return render(request, 'warden.html', context)
        else:
            return HttpResponse('Invalid Login')
    else:
        user = request.user
        if user is not None:
            if not user.is_warden:
                return HttpResponse('Invalid Login')
            else:
                students = Student.objects.all()
                form = VerificationForm(students)
                return render(request, 'document_verification.html', {'form': form, 'students': students})
        else:
            return HttpResponse('Invalid Login')

# @login_required
def warden_add_due(request):
    user = request.user
    if user is not None:
        if not user.is_warden:
            return HttpResponse('Invalid Login')
        else:
            if request.method == "POST":
                form = DuesForm(request.POST)
                if form.is_valid():
                    student = form.cleaned_data.get('choice')
                    student.no_dues = False
                    student.save()
                    messages.error(request,'Dues Added')
                    return redirect('warden_add_due')
            else:
                form = DuesForm()
                return render(request, 'add_due.html', {'form': form})
    else:
        return HttpResponse('Invalid Login')


# @login_required
def warden_remove_due(request):
    user = request.user
    if user is not None:
        if not user.is_warden:
            return HttpResponse('Invalid Login')
        else:
            if request.method == "POST":
                form = NoDuesForm(request.POST)
                if form.is_valid():
                    student = form.cleaned_data.get('choice')
                    student.no_dues = True
                    student.save()
                    messages.error(request,'Dues Cleared')
                    return redirect('warden_add_due')
            else:
                form = NoDuesForm()
                return render(request, 'remove_due.html', {'form': form})
    else:
        return HttpResponse('Invalid Login')




def present_leaves(request):
    user = request.user
    if user is not None:
        if not user.is_warden:
            return HttpResponse('Invalid Login')
        elif user.is_active:
            warden_hostel = user.warden.hostel
            stud = Student.objects.filter(room__hostel=warden_hostel)
            leaves = Leave.objects.filter(student__in=stud,accept=True,start_date__lte=datetime.date.today(), end_date__gte=datetime.date.today()).values_list('student', flat=True).distinct()
            stud = Student.objects.filter(id__in= leaves)
            # print(leaves.query)
            print(stud.query)
            # print(stud)
            return render(request, 'present_leaves.html', {'student': stud})
        else:
            return HttpResponse('Disabled account')
    else:
        return HttpResponse('Invalid Login')


def user_leave(request):
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid() & request.user.student.room_allotted:
            start = form.cleaned_data['start_date']
            end = form.cleaned_data['end_date']
            delta = end- start
            if delta.days > 0 and (start - datetime.date.today()).days >= 0:
                user_contr = Leave.objects.filter(student = request.user.student,start_date__lte=end,end_date__gte=start)
                count = user_contr.count()
                count = int(count)
                if count == 0:
                    leave_form = form.save(commit=False)
                    student = request.user.student
                    leave_form.student = student
                    leave_form.save()
                    leaves = Leave.objects.filter(student = request.user.student)

                    return render(request, 'profile.html', {'student': student,'leaves': leaves})
                else:
                    return HttpResponse('<h3>Already have a Leave in this period Try another</h3>  <br> '
                                        '<a href = \'\' style = "text-align: center; color: Red ;"> Apply Leave </a> ')
            else:
                return HttpResponse('<h2> Invalid Date </h2> <br>  <a href = \'\' '
                                    'style = "text-align: center; color: Red ;"> Apply Leave </a> ')
        elif not request.user.student.room_allotted:
            return HttpResponse('<h3>First Select a Room </h3> <br> <a href = \'select\''
                                ' style = "text-align: center; color: Red ;"> SELECT ROOM </a> ')

        else:
            form = LeaveForm()
            return render(request, 'leave_form.html', {'form': form})
    else:
        if request.user.student.room_allotted:
            form = LeaveForm()
            return render(request, 'leave_form.html', {'form': form})
        else:
            messages.error(request,'Allocate a room first!')
            return redirect('../student_profile/')


def leave_admin(request):
    user = request.user
    if user is not None:
        if not user.is_warden:
            return HttpResponse('Invalid Login')
        else:
            warden_hostel = user.warden.hostel
            stud = Student.objects.filter(room__hostel = warden_hostel)
            # print(stud.values_list('id', flat=True))
            leaves = Leave.objects.filter(student__in=stud).filter(accept=False,reject=False)
            today = datetime.datetime.now().date()
            yesterday = today - datetime.timedelta(15)
            print(today,yesterday)
            accepted_leaves = Leave.objects.filter(student__in=stud,accept=True,
                                                   start_date__lte =today,end_date__gte=yesterday).\
                order_by('-confirm_time')
            print(accepted_leaves)
            return render(request, 'pending.html', {'leaves': leaves,'accepted':accepted_leaves})
    else:
        return HttpResponse('Invalid Login')


def student_leaves(request,std_id):
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(60)
    print(today, yesterday)
    stud = Student.objects.get(id = std_id)
    leaves = Leave.objects.filter(student__id=std_id,accept=True,
                                  start_date__lte=today, end_date__gte=yesterday).order_by('-start_date')
    return render(request, 'student_leave.html', {'leaves': leaves,'student':stud})


def leave_confirm(request,lv_id):
    lv = Leave.objects.get(id = lv_id)
    lv.confirm_time = datetime.datetime.now()
    lv.accept = True
    lv.save()
    return redirect('../../leave')


def leave_reject(request, lv_id):
    lv = Leave.objects.get(id=lv_id)
    lv.reject = True
    lv.save()
    return redirect('../../leave')


def logout_view(request):
    logout(request)
    return redirect('/')

