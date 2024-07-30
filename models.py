from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import app


db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    name = db.Column(db.String(64), index=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), nullable=False)  # 'admin', 'sponsor', 'influencer'
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    influencer = db.relationship('Influencer', backref='user', uselist=False)
    sponsor = db.relationship('Sponsor', backref='user', uselist=False)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Influencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(64), nullable=False)
    category = db.Column(db.String(64))
    niche = db.Column(db.String(64))
    bio = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(120), nullable=True)
    primary_platform = db.Column(db.String(64))
    primary_handle = db.Column(db.String(64))
    secondary_platform = db.Column(db.String(64), nullable=True)
    secondary_handle = db.Column(db.String(64), nullable=True)
    follower_count = db.Column(db.Integer)
    phone_number = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(64), nullable=True)
    reach_metrics = db.Column(db.Text, nullable=True)
    collaboration_types = db.Column(db.Text, nullable=True)
    budget_range = db.Column(db.String(64), nullable=True)


class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(64), nullable=False)
    company_name = db.Column(db.String(64), nullable=True)
    industry = db.Column(db.String(64))
    phone_number = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    budget_range = db.Column(db.String(64), nullable=True)
    collaboration_types = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(64), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)


class AdRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('ad_campaign.id'))
    requirements = db.Column(db.Text)
    payment_amount = db.Column(db.Integer)
    status = db.Column(db.String(64), default='pending')
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    campaign = db.relationship('AdCampaign', foreign_keys=[campaign_id], backref='requests')
    sponsor = db.relationship('User', foreign_keys=[sponsor_id], backref='sponsor_requests')
    influencer = db.relationship('User', foreign_keys=[influencer_id], backref='influencer_requests')
  
    
class AdCampaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    budget = db.Column(db.Integer)
    niche = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)  # Flagging status
    sponsor = db.relationship('User', foreign_keys=[sponsor_id], backref='campaigns')


class InfluencerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    ad_request_id = db.Column(db.Integer, db.ForeignKey('ad_request.id'), nullable=False)
    status = db.Column(db.String(64), default='pending')
    negotiation_budget = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    influencer = db.relationship('Influencer', backref='requests')
    ad_request = db.relationship('AdRequest', backref='requests')
 

# Create database if it doesnt exist
with app.app_context():
    db.create_all()
    
    # Create Admin
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        admin = User(username='admin', name='admin', password='admin', role='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()
