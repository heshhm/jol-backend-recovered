# django_analytics/views.py
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.db.models import Avg, Count, Max, Q
from django.db.models.functions import TruncMinute, TruncHour, TruncDay, TruncYear
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from functools import lru_cache
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import RequestLog, ErrorReportingConfig, ErrorReportEmail, ErrorEmailLog


def _is_superuser(user):
    return user.is_superuser


# === CACHED VIEW DISCOVERY ===
@lru_cache(maxsize=1)
def _discover_views():
    from django.urls import get_resolver
    resolver = get_resolver()
    views = {}
    def collect(patterns, namespace=""):
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                ns = (namespace + pattern.namespace + ":") if pattern.namespace else namespace
                collect(pattern.url_patterns, ns)
            elif hasattr(pattern, 'callback') and pattern.callback:
                name = pattern.name or "unknown"
                full_name = f"{namespace}{name}"
                views[full_name] = {
                    'name': full_name,
                    'url': str(pattern.pattern),
                }
    collect(resolver.url_patterns)
    return views


# === TIME RANGE HELPER ===
def _get_time_range(request):
    range_param = request.GET.get('range', 'today')  # Changed default to 'today'
    now = timezone.now()
    if range_param == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif range_param == 'week':
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif range_param == 'hour':
        start = now - timedelta(hours=1)
        end = now
    else:  # fallback to today
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    return range_param, start, end


# === DYNAMIC TIMELINE + LABELS ===
def _build_timeline(qs, range_param, start, end):
    if range_param == 'hour':
        bucket = TruncMinute('timestamp')
        format_str = '%H:%M'  # Python strftime format: 14:32
        delta = timedelta(minutes=1)
        # Ensure start is truncated to the minute
        if start:
            start = start.replace(second=0, microsecond=0)
        buckets = [(start + delta * i) for i in range(60)]
    elif range_param == 'today':
        bucket = TruncHour('timestamp')
        format_str = '%H:%M'  # Python strftime format: 14:00
        delta = timedelta(hours=1)
        buckets = [(start + delta * i) for i in range(24)]
    elif range_param == 'week':
        bucket = TruncDay('timestamp')
        format_str = '%b %d'  # Python strftime format: Nov 14
        delta = timedelta(days=1)
        # Ensure start is at midnight for proper day bucket matching
        if start:
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        buckets = [(start + delta * i) for i in range(7)]

    def get_series(status_filter):
        q = qs.filter(status_filter).annotate(bucket=bucket).values('bucket').annotate(count=Count('id')).order_by('bucket')
        mapping = {}
        for item in q:
            bucket_time = item['bucket']
            mapping[bucket_time] = item['count']
        
        result = []
        for b in buckets:
            count = mapping.get(b, 0)
            result.append(count)
        
        return result

    success = get_series(Q(status_code__gte=200, status_code__lt=300))
    redirect = get_series(Q(status_code__gte=300, status_code__lt=400))
    client = get_series(Q(status_code__gte=400, status_code__lt=500))
    error = get_series(Q(status_code__gte=500))

    # SAFE LABELS
    labels = []
    for b in buckets:
        if hasattr(b, 'strftime'):  # datetime object
            # Convert to local timezone for display
            from django.utils import timezone as tz
            local_time = tz.localtime(b)
            labels.append(local_time.strftime(format_str))
        else:
            labels.append(str(b))  # fallback

    return success, redirect, client, error, labels


# === MAIN VIEWS ===
@login_required
@user_passes_test(_is_superuser)
def dashboard(request):
    """Full page load"""
    return render(request, "django_analytics/dashboard.html", {
        'content_url': reverse('django_analytics:tab_content'),
        'active_tab': request.GET.get('tab', 'dashboard'),
    })


@login_required
@user_passes_test(_is_superuser)
def tab_content(request):
    """HTMX partials only — BLOCK DIRECT ACCESS"""
    if not request.headers.get('HX-Request'):
        url = reverse('django_analytics:dashboard')
        tab = request.GET.get('tab', 'dashboard')
        return HttpResponseRedirect(f"{url}?tab={tab}")

    tab = request.GET.get('tab', 'dashboard')
    context = {'active_tab': tab}

    if tab == 'dashboard':
        return _render_dashboard_tab(request, context)
    elif tab == 'views':
        return _render_views_tab(request, context)
    elif tab == 'reporting':
        return _render_reporting_tab(request, context)
    elif tab == 'users':
        return _render_users_tab(request, context)
    else:
        return render(request, "django_analytics/partials/empty.html", context)


# === DASHBOARD TAB ===
def _render_dashboard_tab(request, context):
    range_param, start, end = _get_time_range(request)

    # Base queryset
    recent_qs = RequestLog.objects.select_related('user').exclude(view_name__startswith='django_analytics:')

    if start:
        recent_qs = recent_qs.filter(timestamp__gte=start)
    if end:
        recent_qs = recent_qs.filter(timestamp__lte=end)

    # Status filter
    status_filter = request.GET.get('status')
    if status_filter == '2xx':
        recent_qs = recent_qs.filter(status_code__gte=200, status_code__lt=300)
    elif status_filter == '3xx':
        recent_qs = recent_qs.filter(status_code__gte=300, status_code__lt=400)
    elif status_filter == '4xx':
        recent_qs = recent_qs.filter(status_code__gte=400, status_code__lt=500)
    elif status_filter == '5xx':
        recent_qs = recent_qs.filter(status_code__gte=500)

    # Pagination
    page_num = int(request.GET.get('page', 1) or 1)
    paginator = Paginator(recent_qs.order_by('-timestamp'), 25)
    page_obj = paginator.get_page(page_num)

    # Last hour stats (for cards)
    last_hour = timezone.now() - timedelta(hours=1)
    stats_qs = RequestLog.objects.filter(timestamp__gte=last_hour).exclude(view_name__startswith='django_analytics:')
    stats = stats_qs.aggregate(
        total=Count('id'),
        errors=Count('id', filter=Q(status_code__gte=500)),
        avg_duration=Avg('duration_ms'),
    )
    error_rate = (stats['errors'] / stats['total'] * 100) if stats['total'] else 0

    # Timeline
    success_series, redirect_series, client_series, error_series, chart_labels = _build_timeline(
        recent_qs, range_param, start, end
    )

    # Recent error emails (for dashboard preview)
    recent_error_emails = ErrorEmailLog.objects.select_related('request_log').order_by('-sent_at')[:3]

    context.update({
        "recent": page_obj.object_list,
        "page_obj": page_obj,
        "success_series": success_series,
        "redirect_series": redirect_series,
        "client_series": client_series,
        "error_series": error_series,
        "chart_labels": chart_labels,
        "content_url": reverse('django_analytics:tab_content'),
        "error_rate": round(error_rate, 2),
        "avg_duration": round(stats['avg_duration'] or 0, 2),
        "total_requests": stats['total'],
        "current_range": range_param,
        "current_status_filter": status_filter,
        "recent_error_emails": recent_error_emails,
    })
    return render(request, "django_analytics/partials/dashboard_tab.html", context)


# === VIEWS TAB + VIEW DETAIL ===
def _render_views_tab(request, context):
    view_name = request.GET.get('view')
    if view_name:
        # Pass view_name to context for use in partial
        context['view_name'] = view_name
        
        range_param, start, end = _get_time_range(request)
        qs = RequestLog.objects.filter(view_name=view_name)

        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lte=end)

        # Status filter
        status_filter = request.GET.get('status')
        if status_filter == '2xx':
            qs = qs.filter(status_code__gte=200, status_code__lt=300)
        elif status_filter == '3xx':
            qs = qs.filter(status_code__gte=300, status_code__lt=400)
        elif status_filter == '4xx':
            qs = qs.filter(status_code__gte=400, status_code__lt=500)
        elif status_filter == '5xx':
            qs = qs.filter(status_code__gte=500)

        # Stats
        stats = qs.aggregate(
            total_calls=Count('id'),
            avg_duration=Avg('duration_ms'),
            errors=Count('id', filter=Q(status_code__gte=500)),
            last_called=Max('timestamp'),
        )
        total = stats.get('total_calls') or 0
        error_rate = (stats.get('errors', 0) / total * 100) if total else 0

        # Pagination
        page_num = int(request.GET.get('page', 1) or 1)
        recent_qs = qs.select_related('user').order_by('-timestamp')
        paginator = Paginator(recent_qs, 25)
        page_obj = paginator.get_page(page_num)

        # Timeline
        success_series, redirect_series, client_series, error_series, chart_labels = _build_timeline(
            recent_qs, range_param, start, end
        )

        context.update({
            'view_name': view_name,
            'view_stats': {
                'total_calls': total,
                'avg_duration': round(stats.get('avg_duration') or 0, 2),
                'error_rate': round(error_rate or 0, 2),
                'last_called': stats.get('last_called'),
            },
            'recent': page_obj.object_list,
            'page_obj': page_obj,
            'success_series': success_series,
            'redirect_series': redirect_series,
            'client_series': client_series,
            'error_series': error_series,
            'chart_labels': chart_labels,
            'content_url': reverse('django_analytics:tab_content'),
            'current_status_filter': status_filter,
            'current_range': range_param,
        })
        return render(request, 'django_analytics/partials/view_detail.html', context)

    # === LIST ALL VIEWS ===
    all_views = _discover_views()
    view_names = list(all_views.keys())

    stats = (
        RequestLog.objects
        .filter(view_name__in=view_names)
        .values('view_name')
        .annotate(
            avg_duration=Avg('duration_ms'),
            total_calls=Count('id'),
            error_rate=Count('id', filter=Q(status_code__gte=500)) * 100.0 / Count('id'),
            last_called=Max('timestamp'),
        )
    )
    stats_dict = {s['view_name']: s for s in stats}

    view_list = []
    for name, info in all_views.items():
        if ':' in name:
            app = name.split(':', 1)[0]
        else:
            app = 'root'
        stat = stats_dict.get(name, {})
        view_list.append({
            'app': app,
            'name': name,
            'url': info['url'],
            'avg_duration': round(stat.get('avg_duration') or 0, 2),
            'total_calls': stat.get('total_calls') or 0,
            'error_rate': round(stat.get('error_rate') or 0, 2),
            'last_called': stat.get('last_called'),
        })

    apps = sorted({v['app'] for v in view_list})
    
    # Sorting
    sort_by = request.GET.get('sort', 'calls')
    if sort_by == 'calls':
        view_list = sorted(view_list, key=lambda x: x['total_calls'], reverse=True)
    elif sort_by == 'errors':
        view_list = sorted(view_list, key=lambda x: x['error_rate'], reverse=True)
    elif sort_by == 'duration':
        view_list = sorted(view_list, key=lambda x: x['avg_duration'], reverse=True)
    else:
        view_list = sorted(view_list, key=lambda x: x['total_calls'], reverse=True)
    
    context.update({
        'apps': apps,
        'views': view_list,
        'content_url': reverse('django_analytics:tab_content'),
        'current_sort': sort_by,
    })
    return render(request, "django_analytics/partials/views_tab.html", context)


# === REPORTING TAB ===
def _render_reporting_tab(request, context):
    config = ErrorReportingConfig.get_config()
    custom_emails = ErrorReportEmail.objects.filter(active=True).order_by('email')
    
    # Get recent error email logs (only 10 for preview)
    recent_logs = ErrorEmailLog.objects.select_related('request_log').order_by('-sent_at')[:10]
    
    # Stats
    from django.conf import settings
    django_admins = getattr(settings, 'ADMINS', [])
    admin_emails = [admin[1] for admin in django_admins] if django_admins else []
    
    total_recipients = len(custom_emails)
    if config.use_django_admins:
        total_recipients += len(admin_emails)
    
    context.update({
        'config': config,
        'custom_emails': custom_emails,
        'recent_logs': recent_logs,
        'admin_emails': admin_emails,
        'total_recipients': total_recipients,
        'content_url': reverse('django_analytics:tab_content'),
    })
    return render(request, "django_analytics/partials/reporting_tab.html", context)


# === REPORTING ACTIONS ===
@login_required
@user_passes_test(_is_superuser)
def toggle_reporting(request):
    """Toggle error reporting on/off"""
    if request.method == 'POST':
        config = ErrorReportingConfig.get_config()
        config.enabled = not config.enabled
        config.save()
    return HttpResponseRedirect(reverse('django_analytics:tab_content') + '?tab=reporting')


@login_required
@user_passes_test(_is_superuser)
def toggle_django_admins(request):
    """Toggle using Django ADMINS setting"""
    if request.method == 'POST':
        config = ErrorReportingConfig.get_config()
        config.use_django_admins = not config.use_django_admins
        config.save()
    return HttpResponseRedirect(reverse('django_analytics:tab_content') + '?tab=reporting')


@login_required
@user_passes_test(_is_superuser)
def add_email(request):
    """Add custom email address"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()
        
        if email:
            ErrorReportEmail.objects.get_or_create(
                email=email,
                defaults={'name': name, 'created_by': request.user}
            )
    return HttpResponseRedirect(reverse('django_analytics:tab_content') + '?tab=reporting')


@login_required
@user_passes_test(_is_superuser)
def delete_email(request, email_id):
    """Delete custom email address"""
    if request.method == 'POST' or request.method == 'DELETE':
        ErrorReportEmail.objects.filter(id=email_id).delete()
    return HttpResponseRedirect(reverse('django_analytics:tab_content') + '?tab=reporting')


@login_required
@user_passes_test(_is_superuser)
def email_logs_list(request):
    """Paginated list of all error email logs"""
    # Get all error email logs
    logs_qs = ErrorEmailLog.objects.select_related('request_log').order_by('-sent_at')
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter == 'sent':
        logs_qs = logs_qs.filter(success=True)
    elif status_filter == 'failed':
        logs_qs = logs_qs.filter(success=False)
    
    # Pagination (50 per page)
    page_num = int(request.GET.get('page', 1) or 1)
    paginator = Paginator(logs_qs, 50)
    page_obj = paginator.get_page(page_num)
    
    # Stats
    total_sent = ErrorEmailLog.objects.filter(success=True).count()
    total_failed = ErrorEmailLog.objects.filter(success=False).count()
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'total_sent': total_sent,
        'total_failed': total_failed,
        'current_status_filter': status_filter,
    }
    
    # If HTMX request, return partial
    if request.headers.get('HX-Request'):
        return render(request, 'django_analytics/partials/email_logs_list.html', context)
    
    # Otherwise return full page
    return render(request, 'django_analytics/email_logs_list.html', context)

# === USERS TAB ===
def _render_users_tab(request, context):
    """Render users tab with game user profiles"""
    from src.services.user.models import UserProfile
    
    # Get all user profiles with related data
    users_qs = UserProfile.objects.select_related('user').order_by('-id')
    
    # Search filter
    search = request.GET.get('search', '').strip()
    if search:
        users_qs = users_qs.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(referral_code__icontains=search)
        )
    
    # Pagination (20 per page)
    page_num = int(request.GET.get('page', 1) or 1)
    paginator = Paginator(users_qs, 20)
    page_obj = paginator.get_page(page_num)
    
    # Stats
    total_users = UserProfile.objects.count()
    users_with_referrals = UserProfile.objects.filter(total_referrals__gt=0).count()
    
    context.update({
        'page_obj': page_obj,
        'users': page_obj.object_list,
        'total_users': total_users,
        'users_with_referrals': users_with_referrals,
        'search_query': search,
    })
    
    return render(request, "django_analytics/partials/users_tab.html", context)


@login_required
@user_passes_test(_is_superuser)
def user_detail(request, user_id):
    """User detail page showing referral information"""
    from src.services.user.models import UserProfile
    from src.services.game.models import GameHistory
    
    profile = UserProfile.objects.select_related('user', 'referred_by__user').get(id=user_id)
    
    # Get users referred by this user
    referred_users = UserProfile.objects.filter(referred_by=profile).select_related('user').order_by('-id')
    
    # Count games played
    games_played = GameHistory.objects.filter(player=profile.user).count()
    
    context = {
        'profile': profile,
        'referred_users': referred_users,
        'games_played': games_played,
        'content_url': reverse('django_analytics:tab_content'),
    }
    
    # HTMX partial or full page
    if request.headers.get('HX-Request'):
        return render(request, "django_analytics/partials/user_detail.html", context)
    
    return render(request, "django_analytics/user_detail.html", context)
