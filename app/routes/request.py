from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import uuid
from app import db
from app.models.asset_request import AssetRequest
from app.models.satker import Satker
from app.models.asset import Asset
from app.models.prediction import Prediction

request_bp = Blueprint('request', __name__, url_prefix='/request')

@request_bp.route('/')
@login_required
def index():
    """Display all requests for current user's satker"""
    
    satker_id = current_user.satker_id
    
    # Get all requests for the satker
    if current_user.is_admin:
        # Admin can see all requests
        requests = AssetRequest.query.all()
    else:
        # Regular users can only see their satker's requests
        requests = AssetRequest.query.filter_by(satker_id=satker_id).all()
    
    return render_template('requests/index.html', requests=requests)

@request_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new asset request"""
    
    if request.method == 'POST':
        # Get form data
        asset_code = request.form.get('asset_code')
        asset_name = request.form.get('asset_name')
        request_quantity = request.form.get('request_quantity')
        estimated_price = request.form.get('estimated_price')
        fiscal_year = request.form.get('fiscal_year')
        purpose = request.form.get('purpose')
        specification = request.form.get('specification')
        
        # Validate input
        if not asset_code or not asset_name or not request_quantity or not fiscal_year:
            flash('Kode barang, nama barang, jumlah, dan tahun anggaran harus diisi.', 'danger')
            return render_template('requests/create.html')
        
        try:
            request_quantity = int(request_quantity)
            if request_quantity <= 0:
                raise ValueError("Jumlah harus lebih dari 0")
        except ValueError:
            flash('Jumlah harus berupa angka positif.', 'danger')
            return render_template('requests/create.html')
        
        try:
            fiscal_year = int(fiscal_year)
            current_year = datetime.now().year
            if fiscal_year < current_year:
                raise ValueError("Tahun anggaran tidak valid")
        except ValueError:
            flash('Tahun anggaran tidak valid.', 'danger')
            return render_template('requests/create.html')
        
        # Convert estimated price if provided
        if estimated_price:
            try:
                estimated_price = float(estimated_price.replace(',', ''))
            except ValueError:
                flash('Harga perkiraan harus berupa angka.', 'danger')
                return render_template('requests/create.html')
        else:
            estimated_price = None
        
        # Generate unique request ID
        request_id = f"REQ-{current_user.satker.satker_id}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Create new request
        new_request = AssetRequest(
            request_id=request_id,
            satker_id=current_user.satker_id,
            user_id=current_user.id,
            asset_code=asset_code,
            asset_name=asset_name,
            request_quantity=request_quantity,
            estimated_price=estimated_price,
            fiscal_year=fiscal_year,
            purpose=purpose,
            specification=specification,
            status='Draft'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        flash(f'Pengajuan RKBMN dengan ID {request_id} berhasil dibuat.', 'success')
        
        # Redirect to prediction page for the new request
        return redirect(url_for('prediction.create', request_id=new_request.id))
    
    # GET request
    return render_template('requests/create.html')

@request_bp.route('/<int:request_id>')
@login_required
def view(request_id):
    """View details of a specific request"""
    
    asset_request = AssetRequest.query.get_or_404(request_id)
    
    # Check if user has access to this request
    if asset_request.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk melihat pengajuan ini.', 'danger')
        return redirect(url_for('request.index'))
    
    # Get the latest prediction
    latest_prediction = asset_request.predictions.order_by(Prediction.created_at.desc()).first()
    
    return render_template('requests/view.html', request=asset_request, prediction=latest_prediction)

@request_bp.route('/edit/<int:request_id>', methods=['GET', 'POST'])
@login_required
def edit(request_id):
    """Edit an existing request"""
    
    asset_request = AssetRequest.query.get_or_404(request_id)
    
    # Check if user has access to edit this request
    if asset_request.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk mengubah pengajuan ini.', 'danger')
        return redirect(url_for('request.index'))
    
    # Check if request status allows editing
    if asset_request.status != 'Draft':
        flash('Pengajuan yang sudah disubmit tidak dapat diubah.', 'danger')
        return redirect(url_for('request.view', request_id=asset_request.id))
    
    if request.method == 'POST':
        # Get form data
        asset_name = request.form.get('asset_name')
        request_quantity = request.form.get('request_quantity')
        estimated_price = request.form.get('estimated_price')
        fiscal_year = request.form.get('fiscal_year')
        purpose = request.form.get('purpose')
        specification = request.form.get('specification')
        
        # Validate input
        if not asset_name or not request_quantity or not fiscal_year:
            flash('Nama barang, jumlah, dan tahun anggaran harus diisi.', 'danger')
            return render_template('requests/edit.html', request=asset_request)
        
        try:
            request_quantity = int(request_quantity)
            if request_quantity <= 0:
                raise ValueError("Jumlah harus lebih dari 0")
        except ValueError:
            flash('Jumlah harus berupa angka positif.', 'danger')
            return render_template('requests/edit.html', request=asset_request)
        
        try:
            fiscal_year = int(fiscal_year)
            current_year = datetime.now().year
            if fiscal_year < current_year:
                raise ValueError("Tahun anggaran tidak valid")
        except ValueError:
            flash('Tahun anggaran tidak valid.', 'danger')
            return render_template('requests/edit.html', request=asset_request)
        
        # Convert estimated price if provided
        if estimated_price:
            try:
                estimated_price = float(estimated_price.replace(',', ''))
            except ValueError:
                flash('Harga perkiraan harus berupa angka.', 'danger')
                return render_template('requests/edit.html', request=asset_request)
        else:
            estimated_price = None
        
        # Update request
        asset_request.asset_name = asset_name
        asset_request.request_quantity = request_quantity
        asset_request.estimated_price = estimated_price
        asset_request.fiscal_year = fiscal_year
        asset_request.purpose = purpose
        asset_request.specification = specification
        
        db.session.commit()
        
        flash('Pengajuan RKBMN berhasil diperbarui.', 'success')
        
        # Redirect to prediction page for the updated request
        return redirect(url_for('prediction.create', request_id=asset_request.id))
    
    # GET request
    return render_template('requests/edit.html', request=asset_request)

@request_bp.route('/submit/<int:request_id>')
@login_required
def submit(request_id):
    """Submit a request for approval"""
    
    asset_request = AssetRequest.query.get_or_404(request_id)
    
    # Check if user has access to submit this request
    if asset_request.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk mengubah pengajuan ini.', 'danger')
        return redirect(url_for('request.index'))
    
    # Check if request status allows submission
    if asset_request.status != 'Draft':
        flash('Pengajuan ini sudah disubmit sebelumnya.', 'danger')
        return redirect(url_for('request.view', request_id=asset_request.id))
    
    # Update status
    asset_request.status = 'Submitted'
    db.session.commit()
    
    flash('Pengajuan RKBMN berhasil disubmit.', 'success')
    return redirect(url_for('request.view', request_id=asset_request.id))

@request_bp.route('/delete/<int:request_id>')
@login_required
def delete(request_id):
    """Delete a request"""
    
    asset_request = AssetRequest.query.get_or_404(request_id)
    
    # Check if user has access to delete this request
    if asset_request.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk menghapus pengajuan ini.', 'danger')
        return redirect(url_for('request.index'))
    
    # Check if request status allows deletion
    if asset_request.status != 'Draft':
        flash('Pengajuan yang sudah disubmit tidak dapat dihapus.', 'danger')
        return redirect(url_for('request.view', request_id=asset_request.id))
    
    # Delete request and related predictions
    from app.models.prediction import Prediction
    Prediction.query.filter_by(request_id=asset_request.id).delete()
    db.session.delete(asset_request)
    db.session.commit()
    
    flash('Pengajuan RKBMN berhasil dihapus.', 'success')
    return redirect(url_for('request.index'))