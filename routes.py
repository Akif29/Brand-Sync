from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Sponsor, Influencer,AdRequest, AdCampaign, InfluencerRequest
from functools import wraps
from sqlalchemy import func
from app import app
from datetime import datetime

# User auth
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'error')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner

# Role Auth
def role_required(role):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to continue', 'error')
                return redirect(url_for('login'))

            user_id = session['user_id']
            user = User.query.get(user_id)
            
            if user is None or user.role != role:
                flash('You do not have permission to view this page', 'error')
                return redirect(url_for('index'))
            
            return func(*args, **kwargs)
        return inner
    return decorator

@app.route('/')
@auth_required
def index():
    return render_template('index.html', user=User.query.get(session['user_id']))

# Admin Dashboard
@app.route('/admin')
@auth_required
@role_required('admin')
def admin_dash():
    ongoing_campaigns = AdCampaign.query.filter_by(is_active=True).all()
    flagged_users = User.query.filter_by(is_flagged=True).all()
    flagged_campaigns = AdCampaign.query.filter_by(is_flagged=True).all()
    flagged_sponsors = Sponsor.query.filter_by(is_flagged=True).all()
    
    return render_template('admin-dash.html', 
                           user=User.query.get(session['user_id']),
                           ongoing_campaigns=ongoing_campaigns,
                           flagged_users=flagged_users,
                           flagged_campaigns=flagged_campaigns,
                           flagged_sponsors=flagged_sponsors,
                           datetime=datetime)

# Admin Flag    
@app.route('/remove_flag_sponsor/<int:sponsor_id>', methods=['POST'])
def remove_flag_sponsor(sponsor_id):
    sponsor = Sponsor.query.get_or_404(sponsor_id)
    sponsor.is_flagged = False
    db.session.commit()
    flash(f'Flag removed from sponsor {sponsor.name} successfully!', 'success')
    return redirect(url_for('admin_dash'))

@app.route('/remove_flag_user/<int:user_id>', methods=['POST'])
def remove_flag_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_flagged = False
    db.session.commit()
    flash(f'Flag removed from user {user.name} successfully!', 'success')
    return redirect(url_for('admin_dash'))

@app.route('/remove_flag_campaign/<int:campaign_id>', methods=['POST'])
def remove_flag_campaign(campaign_id):
    campaign = AdCampaign.query.get_or_404(campaign_id)
    campaign.is_flagged = False
    db.session.commit()
    flash(f'Flag removed from campaign {campaign.title} successfully!', 'success')
    return redirect(url_for('admin_dash'))

# Admin Find
@app.route('/admin/find', methods=['GET', 'POST'])
@auth_required
@role_required('admin')
def admin_find():
    active_campaigns = AdCampaign.query.filter_by(is_active=True).all()
    active_sponsors = Sponsor.query.all()
    active_users = User.query.filter_by(is_flagged=False).all()  # Example filter for active users, adjust as per your criteria

    return render_template('admin-find.html', user=User.query.get(session['user_id']),active_campaigns=active_campaigns, active_sponsors=active_sponsors, active_users=active_users)

@app.route('/admin/flag_campaign/<int:campaign_id>', methods=['POST'])
@auth_required
@role_required('admin')
def flag_campaign(campaign_id):
    campaign = AdCampaign.query.get_or_404(campaign_id)
    campaign.is_flagged = True
    db.session.commit()
    flash('Campaign flagged successfully.', 'success')
    return redirect(url_for('admin_find'))

@app.route('/admin/flag_sponsor/<int:sponsor_id>', methods=['POST'])
@auth_required
@role_required('admin')
def flag_sponsor(sponsor_id):
    sponsor = Sponsor.query.get_or_404(sponsor_id)
    sponsor.is_flagged = True
    db.session.commit()
    flash('Sponsor flagged successfully.', 'success')
    return redirect(url_for('admin_find'))

@app.route('/admin/flag_user/<int:user_id>', methods=['POST'])
@auth_required
@role_required('admin')
def flag_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_flagged = True
    db.session.commit()
    flash('User flagged successfully.', 'success')
    return redirect(url_for('admin_find'))


# Admin Stats
@app.route('/admin/stats')
@auth_required
@role_required('admin')
def admin_stats():
    total_users = User.query.count()
    total_sponsors = Sponsor.query.count()
    total_influencers = Influencer.query.count()
    total_campaigns = AdCampaign.query.count()
    
    total_budget = db.session.query(func.sum(AdCampaign.budget)).scalar() or 0
    
    flagged_users_count = User.query.filter_by(is_flagged=True).count()
    flagged_campaigns_count = AdCampaign.query.filter_by(is_flagged=True).count()
    flagged_sponsors_count = Sponsor.query.filter_by(is_flagged=True).count()
    
    return render_template('admin-stats.html', 
                           total_users=total_users,
                           total_sponsors=total_sponsors,
                           total_influencers=total_influencers,
                           total_campaigns=total_campaigns,
                           total_budget=total_budget,
                           flagged_users_count=flagged_users_count,
                           flagged_campaigns_count=flagged_campaigns_count,
                           flagged_sponsors_count=flagged_sponsors_count,
                           user=User.query.get(session['user_id']))

# Influencer Dashboard
@app.route('/influencer/dashboard', methods=['GET', 'POST'])
@auth_required
@role_required('influencer')
def influencer_dash():
    user = User.query.get(session['user_id'])
    ad_requests_with_payment = AdRequest.query.filter(AdRequest.influencer_id == user.id, AdRequest.payment_amount.isnot(None)).all()
    influencer = Influencer.query.filter_by(user_id=session['user_id']).first()
    if not influencer:
        flash('Influencer profile not found.', 'danger')
        return redirect(url_for('logout'))
    
    # Query influencer requests for actions
    influencer_requests = InfluencerRequest.query.filter_by(influencer_id=influencer.id).all()
    
    return render_template('influencer-dash.html', user=user, influencer=influencer, ad_requests_with_payment=ad_requests_with_payment, influencer_requests=influencer_requests)

@app.route('/influencer/request/<int:request_id>/accept', methods=['POST'])
@auth_required
@role_required('influencer')
def accept_request_influencer(request_id):
    influencer = Influencer.query.filter_by(user_id=session['user_id']).first()
    influencer_request = InfluencerRequest.query.get(request_id)
    if influencer_request and influencer_request.influencer_id == influencer.id:
        influencer_request.status = 'accepted'
        db.session.commit()
        if influencer_request.ad_request:
                influencer_request.ad_request.status = 'accepted'
                db.session.commit()
    return redirect(url_for('influencer_dash'))

@app.route('/influencer/request/<int:request_id>/reject', methods=['POST'])
@auth_required
@role_required('influencer')
def reject_request_influencer(request_id):
    influencer = Influencer.query.filter_by(user_id=session['user_id']).first()
    influencer_request = InfluencerRequest.query.get(request_id)
    if influencer_request and influencer_request.influencer_id == influencer.id:
        influencer_request.status = 'rejected'
        db.session.commit()
        if influencer_request.ad_request:
            influencer_request.ad_request.status = 'rejected'
            db.session.commit()

    return redirect(url_for('influencer_dash'))

@app.route('/influencer/request/<int:request_id>/negotiate', methods=['POST'])
@auth_required
@role_required('influencer')
def negotiate_request_influencer(request_id):
    influencer = Influencer.query.filter_by(user_id=session['user_id']).first()
    influencer_request = InfluencerRequest.query.get(request_id)
    if influencer_request and influencer_request.influencer_id == influencer.id:
        new_budget = request.form['new_budget']
        influencer_request.negotiation_budget = new_budget
        db.session.commit()
        if influencer_request.ad_request:
            influencer_request.ad_request.budget = new_budget
            db.session.commit()
    return redirect(url_for('influencer_dash'))

# Influencer Find
@app.route('/influencer/find')
@auth_required
@role_required('influencer')
def influencer_find():
    active_campaigns = AdCampaign.query.filter_by(is_active=True).all()
    return render_template('influencer-find.html', user=User.query.get(session['user_id']), campaigns=active_campaigns)


# Request
@app.route('/apply_campaign/<int:campaign_id>', methods=['POST'])
def apply_campaign(campaign_id):
    if 'user_id' not in session:
        flash('You need to login to apply for a campaign', 'error')
        return redirect(url_for('login'))

    influencer_id = session['user_id']
    campaign = AdCampaign.query.get(campaign_id)

    if not campaign:
        flash('Campaign not found', 'error')
        return redirect(url_for('influencer_find'))

    # Check if there's already an existing request for this campaign
    existing_request = AdRequest.query.filter_by(campaign_id=campaign_id, influencer_id=influencer_id).first()
    if existing_request:
        flash('You have already applied for this campaign', 'info')
        return redirect(url_for('influencer_find'))  # Redirect to campaign list or index

    # Create a new request
    new_request = AdRequest(
        sponsor_id=campaign.sponsor_id,
        influencer_id=influencer_id,
        campaign_id=campaign.id,
        requirements=campaign.description,
        payment_amount=campaign.budget,
        status='pending'
    )

    db.session.add(new_request)
    db.session.commit()

    flash('Application submitted successfully', 'success')
    return redirect(url_for('influencer_find'))  # Redirect to campaign list or index

# Influencer Stats
@app.route('/influencer/stats')
@auth_required
@role_required('influencer')
def influencer_stats():
    user_id = session['user_id']
    influencer = User.query.get(user_id).influencer

    # Fetching relevant stats
    total_requests = AdRequest.query.filter_by(influencer_id=user_id).count()
    accepted_requests = AdRequest.query.filter_by(influencer_id=user_id, status='accepted').count()

    # Calculate total earnings (sum of budgets of accepted campaigns)
    total_earnings = db.session.query(db.func.sum(AdCampaign.budget)) \
                               .join(AdRequest, AdRequest.campaign_id == AdCampaign.id) \
                               .filter(AdRequest.influencer_id == user_id, AdRequest.status == 'accepted') \
                               .scalar() or 0

    return render_template('influencer-stats.html', user=User.query.get(session['user_id']), influencer=influencer,
                           total_requests=total_requests, accepted_requests=accepted_requests,
                           total_earnings=total_earnings)
#Influencer Profile
@app.route('/influencer/profile', methods=['GET', 'POST'])
@auth_required
@role_required('influencer')
def influencer_profile():
    user_id = session['user_id']
    influencer = Influencer.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        influencer.name = request.form.get('name') or influencer.name
        influencer.category = request.form.get('category') or influencer.category
        influencer.niche = request.form.get('niche') or influencer.niche
        influencer.bio = request.form.get('bio') or influencer.bio
        influencer.website = request.form.get('website') or influencer.website
        influencer.primary_platform = request.form.get('primary_platform') or influencer.primary_platform
        influencer.primary_handle = request.form.get('primary_handle') or influencer.primary_handle
        influencer.secondary_platform = request.form.get('secondary_platform') or influencer.secondary_platform
        influencer.secondary_handle = request.form.get('secondary_handle') or influencer.secondary_handle
        influencer.follower_count = request.form.get('follower_count') or influencer.follower_count
        influencer.phone_number = request.form.get('phone_number') or influencer.phone_number
        influencer.location = request.form.get('location') or influencer.location
        influencer.reach_metrics = request.form.get('reach_metrics') or influencer.reach_metrics
        influencer.collaboration_types = request.form.get('collaboration_types') or influencer.collaboration_types
        influencer.budget_range = request.form.get('budget_range') or influencer.budget_range

    return render_template('influencer-profile.html', user=User.query.get(session['user_id']), influencer=influencer)

# Influencer Profile Edit
@app.route('/influencer/profile/edit', methods=['GET', 'POST'])
@auth_required
@role_required('influencer')
def influencer_profile_edit():
    user_id = session['user_id']
    influencer = Influencer.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        influencer.name = request.form.get('name') or influencer.name
        influencer.category = request.form.get('category') or influencer.category
        influencer.niche = request.form.get('niche') or influencer.niche
        influencer.bio = request.form.get('bio') or influencer.bio
        influencer.website = request.form.get('website') or influencer.website
        influencer.primary_platform = request.form.get('primary_platform') or influencer.primary_platform
        influencer.primary_handle = request.form.get('primary_handle') or influencer.primary_handle
        influencer.secondary_platform = request.form.get('secondary_platform') or influencer.secondary_platform
        influencer.secondary_handle = request.form.get('secondary_handle') or influencer.secondary_handle
        influencer.follower_count = request.form.get('follower_count') or influencer.follower_count
        influencer.phone_number = request.form.get('phone_number') or influencer.phone_number
        influencer.location = request.form.get('location') or influencer.location
        influencer.reach_metrics = request.form.get('reach_metrics') or influencer.reach_metrics
        influencer.collaboration_types = request.form.get('collaboration_types') or influencer.collaboration_types
        influencer.budget_range = request.form.get('budget_range') or influencer.budget_range

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('influencer_profile'))

    return render_template('influencer-profile-edit.html', user=User.query.get(session['user_id']), influencer=influencer)

# Sponsor Dashboard
@app.route('/sponsor', methods=['GET', 'POST'])
@auth_required
@role_required('sponsor')
def sponsor_dash():
    user = User.query.get(session['user_id'])
    
    # Query ad campaign requests with populated payment fields
    ad_requests_with_payment = AdRequest.query.filter(AdRequest.sponsor_id == user.id, AdRequest.payment_amount.isnot(None)).all()
    
    # Query ad campaign requests without populated payment fields
    ad_requests_without_payment = AdRequest.query.filter(AdRequest.sponsor_id == user.id, AdRequest.payment_amount.is_(None)).all()
    
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')
        
        ad_request = AdRequest.query.get(request_id)
        if ad_request:
            if action == 'accept':
                ad_request.status = 'accepted'
                flash('Campaign request accepted successfully.', 'success')
            elif action == 'reject':
                ad_request.status = 'rejected'
                flash('Campaign request rejected successfully.', 'danger')
            
            db.session.commit()
            return redirect(url_for('sponsor_dash'))
        else:
            flash('Invalid request ID.', 'danger')
    
    return render_template('sponsor-dash.html', user=user, ad_requests_with_payment=ad_requests_with_payment, ad_requests_without_payment=ad_requests_without_payment)


# sponsor Campaign
@app.route('/sponsor/campaign')
@auth_required
@role_required('sponsor')
def sponsor_camp():
    user_id = session['user_id']
    campaigns = AdCampaign.query.filter_by(sponsor_id=user_id).all()
    return render_template('sponsor-camp.html', campaigns=campaigns, user=User.query.get(session['user_id']), datetime=datetime)

# Sponsor Campaign Delete
@app.route('/sponsor/campaign/delete/<int:campaign_id>', methods=['POST'])
@auth_required
@role_required('sponsor')
def delete_campaign(campaign_id):
    campaign = AdCampaign.query.get_or_404(campaign_id)
    if campaign.sponsor_id != session['user_id']:
        flash('You do not have permission to delete this campaign.', 'error')
        return redirect(url_for('sponsor_camp'))

    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully.', 'success')
    return redirect(url_for('sponsor_camp'))

# sponsor Campaign Create
@app.route('/sponsor/campaign/create', methods=['GET', 'POST'])
@auth_required
@role_required('sponsor')
def sponsor_create_camp():
    user_id = session['user_id']
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        budget = request.form['budget']
        niche = request.form['niche']
        created_at = datetime.utcnow()
        
        # Validate end_date against created_at
        if end_date <= created_at:
            flash('End date must be atleast 1 day after start date.', 'error')
            return redirect(url_for('sponsor_create_camp'))
        
        new_campaign = AdCampaign(
            sponsor_id=user_id,
            title=title,
            description=description,
            end_date=end_date,
            budget=budget,
            niche=niche,
            is_active=True
        )
            
        db.session.add(new_campaign)
        db.session.commit()
            
        return redirect(url_for('sponsor_camp'))
    return render_template('sponsor-camp-create.html', user=User.query.get(session['user_id']))

@app.route('/sponsor/request/<int:request_id>/accept', methods=['POST'])
@auth_required
@role_required('sponsor')
def accept_request(request_id):
    ad_request = AdRequest.query.get(request_id)
    if ad_request and ad_request.sponsor_id == session['user_id']:
        ad_request.status = 'accepted'
        db.session.commit()
        flash('Request accepted successfully.', 'success')
    return redirect(url_for('sponsor_dash'))

@app.route('/sponsor/request/<int:request_id>/reject', methods=['POST'])
@auth_required
@role_required('sponsor')
def reject_request(request_id):
    ad_request = AdRequest.query.get(request_id)
    if ad_request and ad_request.sponsor_id == session['user_id']:
        ad_request.status = 'rejected'
        db.session.commit()
        flash('Request rejected successfully.', 'success')
    return redirect(url_for('sponsor_dash'))

# sponsor Stats
@app.route('/sponsor/stats')
@auth_required  
@role_required('sponsor')  
def sponsor_stats():
    user_id = session['user_id']
    sponsor = User.query.get(user_id).sponsor

    # Fetching relevant stats
    total_active_campaigns = AdCampaign.query \
        .filter(AdCampaign.sponsor_id == user_id, AdCampaign.is_active == True, AdCampaign.end_date >= datetime.utcnow()) \
        .count()

    total_influencers_hired = db.session.query(Influencer) \
        .join(AdRequest, Influencer.user_id == AdRequest.influencer_id) \
        .filter(AdRequest.sponsor_id == user_id, AdRequest.status == 'accepted') \
        .distinct(Influencer.id) \
        .count()
        
    total_spend = db.session.query(db.func.sum(AdCampaign.budget)).filter_by(sponsor_id=user_id).scalar() or 0


    return render_template('sponsor-stats.html', user=User.query.get(session['user_id']), sponsor=sponsor,
                           total_active_campaigns=total_active_campaigns, total_influencers_hired=total_influencers_hired, total_spend=total_spend)

# Sponsor Profile 
@app.route('/sponsor/profile', methods=['GET', 'POST'])
@auth_required
@role_required('sponsor')
def sponsor_profile():
    user_id = session['user_id']
    sponsor = Sponsor.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        sponsor.name = request.form.get('name') or sponsor.name
        sponsor.company_name = request.form.get('company_name') or sponsor.company_name
        sponsor.industry = request.form.get('industry') or sponsor.industry
        sponsor.phone_number = request.form.get('phone_number') or sponsor.phone_number
        sponsor.website = request.form.get('website') or sponsor.website
        sponsor.bio = request.form.get('bio') or sponsor.bio
        sponsor.phone_number = request.form.get('phone_number') or sponsor.phone_number
        sponsor.location = request.form.get('location') or sponsor.location
        sponsor.collaboration_types = request.form.get('collaboration_types') or sponsor.collaboration_types
        sponsor.budget_range = request.form.get('budget_range') or sponsor.budget_range

    return render_template('sponsor-profile.html', user=User.query.get(session['user_id']), sponsor=sponsor)

# Sponsor Profile Create
@app.route('/sponsor/find/edit', methods=['GET', 'POST'])
@auth_required
@role_required('sponsor')
def sponsor_profile_edit():
    user_id = session['user_id']
    sponsor = Sponsor.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        sponsor.name = request.form.get('name') or sponsor.name
        sponsor.company_name = request.form.get('company_name') or sponsor.company_name
        sponsor.industry = request.form.get('industry') or sponsor.industry
        sponsor.phone_number = request.form.get('phone_number') or sponsor.phone_number
        sponsor.website = request.form.get('website') or sponsor.website
        sponsor.bio = request.form.get('bio') or sponsor.bio
        sponsor.phone_number = request.form.get('phone_number') or sponsor.phone_number
        sponsor.location = request.form.get('location') or sponsor.location
        sponsor.collaboration_types = request.form.get('collaboration_types') or sponsor.collaboration_types
        sponsor.budget_range = request.form.get('budget_range') or sponsor.budget_range

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('sponsor_profile'))

    return render_template('sponsor-profile-edit.html', user=User.query.get(session['user_id']), sponsor=sponsor)

# Sponsor Find
@app.route('/sponsor/find', methods=['GET', 'POST'])
@auth_required
@role_required('sponsor')
def sponsor_find():
    user_id = session['user_id']
    search_query = ""
    if request.method == 'POST':
        search_query = request.form.get('search', '').strip()
        influencers = Influencer.query.filter(
            (Influencer.name.ilike(f'%{search_query}%')) |
            (Influencer.category.ilike(f'%{search_query}%')) |
            (Influencer.niche.ilike(f'%{search_query}%'))
            ).all()
    else:
        influencers = Influencer.query.all()  # Get all influencers by default
        
    return render_template('sponsor-find.html', user=User.query.get(session['user_id']),influencers=influencers, search_query=search_query)

@app.route('/request_influencer/<int:influencer_id>', methods=['POST'])
@auth_required
@role_required('sponsor')
def request_influencer(influencer_id):
    # Check if the influencer exists
    influencer = Influencer.query.get(influencer_id)
    if not influencer:
        flash('Influencer not found.', 'danger')
        return redirect(url_for('sponsor_find'))

    # Create an AdRequest and link it to the sponsor (current user)
    ad_request = AdRequest(
        sponsor_id=session['user_id'],
        influencer_id=influencer.user_id,
        status='pending'
    )
    db.session.add(ad_request)
    db.session.commit()

    # Create the InfluencerRequest
    influencer_request = InfluencerRequest(
        influencer_id=influencer_id,
        ad_request_id=ad_request.id,
        status='pending'
    )
    db.session.add(influencer_request)
    db.session.commit()

    # Flash a message to inform the user that the request was successful
    flash('Influencer request sent successfully!', 'success')
    return redirect(url_for('sponsor_find'))

@app.route('/sponsor/request/<int:request_id>/negotiate', methods=['POST'])
@auth_required
@role_required('sponsor')
def negotiate_request_sponsor(request_id):
    ad_request = AdRequest.query.get_or_404(request_id)
    if ad_request and ad_request.sponsor_id == session['user_id']:
        new_budget = request.form.get('new_budget')
        if new_budget:
            ad_request.payment_amount = int(new_budget)
            ad_request.status = 'negotiating'
            db.session.commit()
    return redirect(url_for('sponsor_dash'))


@app.route('/edit_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@auth_required
@role_required('sponsor')
def edit_campaign(campaign_id):
    campaign = AdCampaign.query.get_or_404(campaign_id)
    
    if request.method == 'POST':
        # Update campaign details
        campaign.title = request.form['title']
        campaign.description = request.form['description']
        campaign.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        campaign.budget = request.form['budget']
        campaign.niche = request.form['niche']
        campaign.is_active = 'is_active' in request.form
        
        ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
        for ad_request in ad_requests:
            ad_request.payment_amount = campaign.budget 
        
        db.session.commit()
        flash('Campaign updated successfully!', 'success')
        return redirect(url_for('sponsor_camp'))
    
    return render_template('edit_campaign.html', user=User.query.get(session['user_id']), campaign=campaign)



# Login
@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/login", methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if username == '' or password == '':
        flash('Username or Password cannot be empty', 'error')
        return redirect(url_for('login'))
    if not user:
        flash('User does not exist.', 'error')
        return redirect(url_for('login'))
    if not user.check_password(password):
        flash('Incorrect Password.', 'error')
        return redirect(url_for('login'))
    # login successful
    session['user_id'] = user.id
    
        # Redirect to the respective dashboard based on user role
    if user.role == 'admin':
        return redirect(url_for('admin_dash'))
    if user.role == 'influencer':
        return redirect(url_for('influencer_dash'))
    if user.role == 'sponsor':
        return redirect(url_for('sponsor_dash'))
        # Default redirect if no role matches
    return redirect(url_for('index'))

# Sign Up
@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route("/signup", methods=['POST'])
def signup_post():
    name = request.form.get('name')
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    if username == '':
        flash('Username cannot be empty', 'error')
        return redirect(url_for('signup'))
    if password == '':
        flash('Password cannot be empty', 'error')
        return redirect(url_for('signup'))
    if name == '':
        flash('Name cannot be empty', 'error')
        return redirect(url_for('signup'))
    
    # Check if username is valid
    if User.query.filter_by(username=username).first():
        flash('Username has been taken', 'error')
        return redirect(url_for('signup'))
    
    # valid username
    user = User(name=name, username=username, password=password, role=role)
    db.session.add(user)
    db.session.commit()
    
    if role == 'influencer':
        influencer = Influencer(user_id=user.id, name=name)
        db.session.add(influencer)
        db.session.commit()
    elif role == 'sponsor':
        sponsor = Sponsor(user_id=user.id, name=name)
        db.session.add(sponsor)
        db.session.commit()
        
    
    flash('User successfully registered.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))
