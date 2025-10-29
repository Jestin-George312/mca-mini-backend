from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import render

# --- Add these imports for the graph ---
import io
import base64
import matplotlib.pyplot as plt
from django.contrib.admin.views.decorators import staff_member_required

# This is your existing view for the index page
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta

def my_admin_index(request, extra_context=None):
    """
    This is our custom admin index view.
    It calculates analytics and passes them to the original admin index view.
    """
    
    # --- Calculate User Stats ---
    thirty_days_ago = now() - timedelta(days=30)
    
    total_users = User.objects.count()
    
    active_users = User.objects.filter(
        last_login__gte=thirty_days_ago
    ).count()
    
    passive_users = total_users - active_users
    # --- End of Calculations ---
    
    # Prepare the context to pass to the template
    if extra_context is None:
        extra_context = {}
        
    extra_context['total_users'] = total_users
    extra_context['active_users'] = active_users
    extra_context['passive_users'] = passive_users
    
    # Call the original admin index view with our new context
    return admin.site.index(request, extra_context)


# --- ADD THIS NEW VIEW ---
@staff_member_required # Ensures only staff can see this page
def user_graph_view(request):
    """
    This view generates the user activity graph.
    """
    # 1. Get the same data
    thirty_days_ago = now() - timedelta(days=30)
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()
    passive_users = total_users - active_users

    # 2. Generate the graph with Matplotlib
    labels = [ 'Passive Users','Active Users']
    counts = [active_users, passive_users]

    fig, ax = plt.subplots()
    ax.bar(labels, counts, color=['#F44336','#4CAF50'])
    ax.set_ylabel('Number of Users')
    ax.set_title('User Activity (Last 30 Days)')
    
    # 3. Save graph to a memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    
    # 4. Encode image in base64 to pass to the template
    graph_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    # 5. Render the template
    context = {
        'title': 'User Activity Graph',
        'graph_data': graph_data,
        **admin.site.each_context(request), # Adds default admin context
    }
    return render(request, 'admin/user_graph.html', context)