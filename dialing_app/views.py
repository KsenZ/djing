from datetime import datetime
from subprocess import run
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.shortcuts import render_to_text
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from guardian.decorators import permission_required_or_403 as permission_required
from django.db.models import Q

from abonapp.models import Abon
from mydefs import only_admins, pag_mn
from .models import AsteriskCDR, SMSModel
from .forms import SMSOutForm


@login_required
@permission_required('dialing_app.change_asteriskcdr')
def home(request):
    logs = AsteriskCDR.objects.exclude(userfield='request').order_by('-calldate')
    logs = pag_mn(request, logs)
    title = _('Last calls')
    return render(request, 'index.html', {
        'logs': logs,
        'title': title
    })


@login_required
@only_admins
def to_abon(request, tel):
    abon = Abon.objects.filter(telephone=tel)
    abon_count = abon.count()
    if abon_count > 1:
        messages.warning(request, _('Multiple users with the telephone number'))
    elif abon_count == 0:
        messages.error(request, _('User with the telephone number not found'))
        return redirect('dialapp:home')
    abon = abon[0]
    if abon.group:
        return redirect('abonapp:abon_home', gid=abon.group.pk, uid=abon.pk)
    else:
        return redirect('abonapp:group_list')


@login_required
@only_admins
def vmail_request(request):
    title = _('Voice mail request')
    cdr = AsteriskCDR.objects.filter(userfield='request').order_by('-calldate')
    cdr = pag_mn(request, cdr)
    return render(request, 'vmail.html', {
        'title': title,
        'vmessages': cdr
    })

@login_required
@only_admins
def vmail_report(request):
    title = _('Voice mail report')
    cdr = AsteriskCDR.objects.filter(userfield='report').order_by('-calldate')
    cdr = pag_mn(request, cdr)
    return render(request, 'vmail.html', {
        'title': title,
        'vmessages': cdr
    })


@login_required
@only_admins
def vfilter(request):
    cdr_q = None
    sd = request.GET.get('sd')
    s = request.GET.get('s')
    if s:
        cdr_q = Q(src__icontains=s) | Q(dst__icontains=s)

    try:
        if sd:
            sd_date = datetime.strptime(sd, '%Y-%m-%d')
            if cdr_q:
                cdr_q |= Q(calldate__date=sd_date)
            else:
                cdr_q = Q(calldate__date=sd_date)
    except ValueError:
        messages.error(request, _('Make sure that your date format is correct'))

    if cdr_q is None:
        cdr = AsteriskCDR.objects.all()
    else:
        cdr = AsteriskCDR.objects.filter(cdr_q)
    cdr = pag_mn(request, cdr)
    return render(request, 'index.html', {
        'logs': cdr,
        'title': _('Find dials'),
        's': s,
        'sd': sd
    })


@login_required
@permission_required('dialing_app.can_view_sms')
def inbox_sms(request):
    msgs = SMSModel.objects.all().order_by('-when')
    msgs = pag_mn(request, msgs)
    return render(request, 'inbox_sms.html', {
        'sms_messages': msgs
    })


@login_required
@permission_required('dialing_app.can_send_sms')
def send_sms(request):
    path = request.GET.get('path')
    initial_dst = request.GET.get('dst')
    if request.method == 'POST':
        frm = SMSOutForm(request.POST)
        if frm.is_valid():
            frm.save()
            messages.success(request, _('Message was enqueued for sending'))
            try:
                pidfile_name = '/run/dialing.py.pid'
                with open(pidfile_name, 'r') as f:
                    pid = int(f.read())
                run(['/usr/bin/kill', '-SIGUSR1', str(pid)])
            except FileNotFoundError:
                print('Failed sending, %s not found' % pidfile_name)
            if path:
                return redirect(path)
            else:
                return redirect('dialapp:inbox_sms')
        else:
            messages.error(request, _('fix form errors'))
    else:
        frm = SMSOutForm(initial={'dst': initial_dst})
    return render_to_text('modal_send_sms.html', {
        'form': frm,
        'path': path
    }, request=request)
