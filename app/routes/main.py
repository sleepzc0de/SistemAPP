from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.asset_request import AssetRequest
from app.models.asset import Asset
from app.models.prediction import Prediction
from app.models.satker import Satker
import json
from sqlalchemy import func
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Dashboard page"""
    
    satker_id = current_user.satker_id
    
    # Dashboard data
    dashboard_data = {}
    
    # Get counts for assets
    if current_user.is_admin:
        # Admin sees all data
        asset_count = Asset.query.count()
        asset_good = Asset.query.filter_by(asset_condition='Baik').count()
        asset_minor = Asset.query.filter_by(asset_condition='Rusak Ringan').count()
        asset_major = Asset.query.filter_by(asset_condition='Rusak Berat').count()
        
        # Get counts for requests
        request_total = AssetRequest.query.count()
        request_draft = AssetRequest.query.filter_by(status='Draft').count()
        request_submitted = AssetRequest.query.filter_by(status='Submitted').count()
        request_approved = AssetRequest.query.filter_by(status='Approved').count()
        request_rejected = AssetRequest.query.filter_by(status='Rejected').count()
        
        # Get counts for predictions
        prediction_total = Prediction.query.count()
        prediction_approved = Prediction.query.filter_by(prediction_result=True).count()
        prediction_rejected = Prediction.query.filter_by(prediction_result=False).count()
        
        # Get satker data
        satker_count = Satker.query.count()
        total_employees = db.session.query(func.sum(Satker.employee_count)).scalar() or 0
    else:
        # User sees only their satker's data
        asset_count = Asset.query.filter_by(satker_id=satker_id).count()
        asset_good = Asset.query.filter_by(satker_id=satker_id, asset_condition='Baik').count()
        asset_minor = Asset.query.filter_by(satker_id=satker_id, asset_condition='Rusak Ringan').count()
        asset_major = Asset.query.filter_by(satker_id=satker_id, asset_condition='Rusak Berat').count()
        
        # Get counts for requests
        request_total = AssetRequest.query.filter_by(satker_id=satker_id).count()
        request_draft = AssetRequest.query.filter_by(satker_id=satker_id, status='Draft').count()
        request_submitted = AssetRequest.query.filter_by(satker_id=satker_id, status='Submitted').count()
        request_approved = AssetRequest.query.filter_by(satker_id=satker_id, status='Approved').count()
        request_rejected = AssetRequest.query.filter_by(satker_id=satker_id, status='Rejected').count()
        
        # Get counts for predictions
        prediction_total = Prediction.query.join(AssetRequest).filter(AssetRequest.satker_id == satker_id).count()
        prediction_approved = Prediction.query.join(AssetRequest).filter(
            AssetRequest.satker_id == satker_id,
            Prediction.prediction_result == True
        ).count()
        prediction_rejected = Prediction.query.join(AssetRequest).filter(
            AssetRequest.satker_id == satker_id,
            Prediction.prediction_result == False
        ).count()
        
        # Get satker data
        satker_count = 1
        total_employees = current_user.satker.employee_count
    
    # Calculate percentages
    asset_good_percent = (asset_good / asset_count) * 100 if asset_count > 0 else 0
    asset_minor_percent = (asset_minor / asset_count) * 100 if asset_count > 0 else 0
    asset_major_percent = (asset_major / asset_count) * 100 if asset_count > 0 else 0
    
    prediction_approved_percent = (prediction_approved / prediction_total) * 100 if prediction_total > 0 else 0
    prediction_rejected_percent = (prediction_rejected / prediction_total) * 100 if prediction_total > 0 else 0
    
    # Get recent activity
    if current_user.is_admin:
        recent_requests = AssetRequest.query.order_by(AssetRequest.created_at.desc()).limit(5).all()
        recent_predictions = Prediction.query.order_by(Prediction.created_at.desc()).limit(5).all()
    else:
        recent_requests = AssetRequest.query.filter_by(satker_id=satker_id).order_by(
            AssetRequest.created_at.desc()
        ).limit(5).all()
        recent_predictions = Prediction.query.join(AssetRequest).filter(
            AssetRequest.satker_id == satker_id
        ).order_by(Prediction.created_at.desc()).limit(5).all()
    
    # Dashboard data
    dashboard_data = {
        'asset': {
            'count': asset_count,
            'good': asset_good,
            'good_percent': asset_good_percent,
            'minor': asset_minor,
            'minor_percent': asset_minor_percent,
            'major': asset_major,
            'major_percent': asset_major_percent
        },
        'request': {
            'total': request_total,
            'draft': request_draft,
            'submitted': request_submitted,
            'approved': request_approved,
            'rejected': request_rejected
        },
        'prediction': {
            'total': prediction_total,
            'approved': prediction_approved,
            'approved_percent': prediction_approved_percent,
            'rejected': prediction_rejected,
            'rejected_percent': prediction_rejected_percent
        },
        'satker': {
            'count': satker_count,
            'total_employees': total_employees
        },
        'recent_requests': recent_requests,
        'recent_predictions': recent_predictions
    }
    
    return render_template('dashboard/index.html', dashboard=dashboard_data)

@main_bp.route('/statistics')
@login_required
def statistics():
    """Statistics page"""
    
    satker_id = current_user.satker_id
    
    # Get date range (last 12 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Get monthly data
    monthly_data = []
    
    current_date = start_date
    while current_date <= end_date:
        month_start = datetime(current_date.year, current_date.month, 1)
        if current_date.month == 12:
            month_end = datetime(current_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
        
        # Get request counts for this month
        if current_user.is_admin:
            month_requests = AssetRequest.query.filter(
                AssetRequest.created_at >= month_start,
                AssetRequest.created_at <= month_end
            ).count()
            
            month_predictions = Prediction.query.filter(
                Prediction.created_at >= month_start,
                Prediction.created_at <= month_end
            ).count()
            
            month_approved = Prediction.query.filter(
                Prediction.created_at >= month_start,
                Prediction.created_at <= month_end,
                Prediction.prediction_result == True
            ).count()
            
            month_rejected = Prediction.query.filter(
                Prediction.created_at >= month_start,
                Prediction.created_at <= month_end,
                Prediction.prediction_result == False
            ).count()
        else:
            month_requests = AssetRequest.query.filter_by(satker_id=satker_id).filter(
                AssetRequest.created_at >= month_start,
                AssetRequest.created_at <= month_end
            ).count()
            
            month_predictions = Prediction.query.join(AssetRequest).filter(
                AssetRequest.satker_id == satker_id,
                Prediction.created_at >= month_start,
                Prediction.created_at <= month_end
            ).count()
            
            month_approved = Prediction.query.join(AssetRequest).filter(
                AssetRequest.satker_id == satker_id,
                Prediction.created_at >= month_start,
                Prediction.created_at <= month_end,
                Prediction.prediction_result == True
            ).count()
            
            month_rejected = Prediction.query.join(AssetRequest).filter(
                AssetRequest.satker_id == satker_id,
                Prediction.created_at >= month_start,
                Prediction.created_at <= month_end,
                Prediction.prediction_result == False
            ).count()
        
        monthly_data.append({
            'month': current_date.strftime('%b %Y'),
            'requests': month_requests,
            'predictions': month_predictions,
            'approved': month_approved,
            'rejected': month_rejected
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
    
    # Get top asset codes
    if current_user.is_admin:
        top_asset_codes = db.session.query(
            AssetRequest.asset_code,
            func.count(AssetRequest.id).label('count')
        ).group_by(AssetRequest.asset_code).order_by(func.count(AssetRequest.id).desc()).limit(10).all()
    else:
        top_asset_codes = db.session.query(
            AssetRequest.asset_code,
            func.count(AssetRequest.id).label('count')
        ).filter_by(satker_id=satker_id).group_by(AssetRequest.asset_code).order_by(
            func.count(AssetRequest.id).desc()
        ).limit(10).all()
    
    # Format for chart
    chart_data = {
        'monthly': monthly_data,
        'top_asset_codes': [{'code': code, 'count': count} for code, count in top_asset_codes]
    }
    
    return render_template('dashboard/statistics.html', chart_data=chart_data)

@main_bp.route('/about')
@login_required
def about():
    """About page"""
    return render_template('dashboard/about.html')