from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.asset import Asset
from app.models.satker import Satker
from app.services.external_service import ExternalService

asset_bp = Blueprint('asset', __name__, url_prefix='/asset')

@asset_bp.route('/')
@login_required
def index():
    # Get assets for current user's satker
    satker_id = current_user.satker_id
    assets = Asset.query.filter_by(satker_id=satker_id).all()
    
    return render_template('assets/index.html', assets=assets)

@asset_bp.route('/<int:asset_id>')
@login_required
def view(asset_id):
    # Get asset details
    asset = Asset.query.get_or_404(asset_id)
    
    # Check if user has access to this asset
    if asset.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk melihat aset ini.', 'danger')
        return redirect(url_for('asset.index'))
    
    return render_template('assets/view.html', asset=asset)

@asset_bp.route('/sync')
@login_required
def sync():
    """Synchronize assets with external systems (SIMAN/SAKTI)"""
    
    # Only admin can trigger sync
    if not current_user.is_admin:
        flash('Anda tidak memiliki hak akses untuk operasi ini.', 'danger')
        return redirect(url_for('asset.index'))
    
    try:
        # Initialize external service
        external_service = ExternalService()
        
        # Sync assets from SIMAN
        result = external_service.sync_assets_from_siman(current_user.satker_id)
        
        if result['success']:
            flash(f'Berhasil menyinkronkan {result["count"]} aset dari SIMAN.', 'success')
        else:
            flash(f'Gagal menyinkronkan aset dari SIMAN: {result["message"]}', 'danger')
        
        return redirect(url_for('asset.index'))
        
    except Exception as e:
        flash(f'Terjadi kesalahan saat sinkronisasi: {str(e)}', 'danger')
        return redirect(url_for('asset.index'))

@asset_bp.route('/search')
@login_required
def search():
    """Search assets by code or name"""
    
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('asset.index'))
    
    # Search assets for current user's satker
    satker_id = current_user.satker_id
    
    # Search by asset code or name
    assets = Asset.query.filter_by(satker_id=satker_id).filter(
        (Asset.asset_code.contains(query)) | 
        (Asset.asset_name.contains(query))
    ).all()
    
    return render_template('assets/index.html', assets=assets, query=query)

@asset_bp.route('/update_condition/<int:asset_id>', methods=['POST'])
@login_required
def update_condition(asset_id):
    """Update asset condition"""
    
    # Get asset
    asset = Asset.query.get_or_404(asset_id)
    
    # Check if user has access to this asset
    if asset.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk mengubah aset ini.', 'danger')
        return redirect(url_for('asset.index'))
    
    # Get new condition from form
    new_condition = request.form.get('condition')
    if not new_condition or new_condition not in ['Baik', 'Rusak Ringan', 'Rusak Berat']:
        flash('Kondisi aset tidak valid.', 'danger')
        return redirect(url_for('asset.view', asset_id=asset_id))
    
    # Update condition
    asset.asset_condition = new_condition
    db.session.commit()
    
    flash('Kondisi aset berhasil diperbarui.', 'success')
    return redirect(url_for('asset.view', asset_id=asset_id))

@asset_bp.route('/get_by_code/<string:asset_code>')
@login_required
def get_by_code(asset_code):
    """Get asset details by asset code (AJAX endpoint)"""
    
    satker_id = current_user.satker_id
    
    # Get assets with this code
    assets = Asset.query.filter_by(satker_id=satker_id, asset_code=asset_code).all()
    
    # Format for JSON response
    assets_data = []
    for asset in assets:
        assets_data.append({
            'id': asset.id,
            'asset_id': asset.asset_id,
            'asset_name': asset.asset_name,
            'asset_condition': asset.asset_condition,
            'acquisition_date': asset.acquisition_date.strftime('%Y-%m-%d') if asset.acquisition_date else None,
            'acquisition_value': float(asset.acquisition_value) if asset.acquisition_value else None
        })
    
    return jsonify({
        'success': True,
        'count': len(assets_data),
        'assets': assets_data
    })