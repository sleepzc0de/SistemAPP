from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
import json
import io
from datetime import datetime
from app import db
from app.models.asset_request import AssetRequest
from app.models.prediction import Prediction
from app.services.prediction_service import PredictionService

prediction_bp = Blueprint('prediction', __name__, url_prefix='/prediction')

@prediction_bp.route('/')
@login_required
def index():
    """Display all predictions for current user's satker"""
    
    satker_id = current_user.satker_id
    
    # Get all predictions for the satker
    if current_user.is_admin:
        # Admin can see all predictions
        predictions = Prediction.query.join(AssetRequest).all()
    else:
        # Regular users can only see their satker's predictions
        predictions = Prediction.query.join(AssetRequest).filter(AssetRequest.satker_id == satker_id).all()
    
    return render_template('predictions/index.html', predictions=predictions)

@prediction_bp.route('/create/<int:request_id>')
@login_required
def create(request_id):
    """Create a new prediction for a request"""
    
    # Get the request
    asset_request = AssetRequest.query.get_or_404(request_id)
    
    # Check if user has access to this request
    if asset_request.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk memprediksi pengajuan ini.', 'danger')
        return redirect(url_for('request.index'))
    
    # Check if the request already has a prediction
    existing_prediction = asset_request.predictions.order_by(Prediction.created_at.desc()).first()
    
    # If there's an existing prediction and the request hasn't changed, use that
    # For now, always generate a new prediction
    
    # Generate prediction
    prediction_service = PredictionService()
    prediction = prediction_service.generate_prediction(asset_request)
    
    # Redirect to result page
    return redirect(url_for('prediction.result', prediction_id=prediction.id))

@prediction_bp.route('/result/<int:prediction_id>')
@login_required
def result(prediction_id):
    """Display prediction result"""
    
    # Get the prediction
    prediction = Prediction.query.get_or_404(prediction_id)
    
    # Check if user has access to this prediction
    if prediction.asset_request.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk melihat prediksi ini.', 'danger')
        return redirect(url_for('prediction.index'))
    
    # Load details from JSON if stored as string
    if prediction.details and isinstance(prediction.details, str):
        details = json.loads(prediction.details)
    else:
        details = prediction.details or {}
    
    # Get recommendation
    recommendation = prediction.get_recommendation()
    
    # Get reasoning
    reasoning = prediction.explain_reasoning()
    
    return render_template('predictions/result.html', 
                          prediction=prediction, 
                          details=details,
                          recommendation=recommendation,
                          reasoning=reasoning)

@prediction_bp.route('/api/check/<int:request_id>')
@login_required
def api_check(request_id):
    """API endpoint to check prediction for a request"""
    
    # Get the request
    asset_request = AssetRequest.query.get_or_404(request_id)
    
    # Check if user has access to this request
    if asset_request.satker_id != current_user.satker_id and not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Unauthorized access'
        }), 403
    
    # Generate prediction
    prediction_service = PredictionService()
    prediction = prediction_service.generate_prediction(asset_request)
    
    # Format response
    if prediction.details and isinstance(prediction.details, str):
        details = json.loads(prediction.details)
    else:
        details = prediction.details or {}
    
    return jsonify({
        'success': True,
        'prediction': {
            'id': prediction.id,
            'request_id': prediction.request_id,
            'result': prediction.prediction_result,
            'confidence': prediction.confidence_level,
            'details': details,
            'recommendation': prediction.get_recommendation(),
            'reasoning': prediction.explain_reasoning(),
            'created_at': prediction.created_at.isoformat()
        }
    })

@prediction_bp.route('/export/<int:prediction_id>')
@login_required
def export(prediction_id):
    """Export prediction result as PDF"""
    
    # Get the prediction
    prediction = Prediction.query.get_or_404(prediction_id)
    
    # Check if user has access to this prediction
    if prediction.asset_request.satker_id != current_user.satker_id and not current_user.is_admin:
        flash('Anda tidak memiliki akses untuk mengekspor prediksi ini.', 'danger')
        return redirect(url_for('prediction.index'))
    
    # Get the asset request
    asset_request = prediction.asset_request
    
    try:
        # Import libraries for PDF generation
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        
        # Create a buffer to store the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=1,  # Center alignment
            spaceAfter=12
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=6,
            spaceAfter=6
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        
        # Create the document content
        content = []
        
        # Add title
        content.append(Paragraph("HASIL PREDIKSI PENGAJUAN RKBMN", title_style))
        content.append(Spacer(1, 0.5 * cm))
        
        # Add request details
        content.append(Paragraph("INFORMASI PENGAJUAN", subtitle_style))
        request_data = [
            ["ID Pengajuan", asset_request.request_id],
            ["Satuan Kerja", asset_request.satker.satker_name],
            ["Kode Barang", asset_request.asset_code],
            ["Nama Barang", asset_request.asset_name],
            ["Jumlah", str(asset_request.request_quantity)],
            ["Tahun Anggaran", str(asset_request.fiscal_year)],
            ["Tanggal Pengajuan", asset_request.created_at.strftime("%d %B %Y %H:%M")]
        ]
        
        # Create table for request details
        request_table = Table(request_data, colWidths=[4 * cm, 12 * cm])
        request_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        content.append(request_table)
        content.append(Spacer(1, 0.5 * cm))
        
        # Add prediction result
        content.append(Paragraph("HASIL PREDIKSI", subtitle_style))
        
        # Format prediction result
        result_text = "Disetujui" if prediction.prediction_result else "Ditolak"
        confidence = f"{prediction.confidence_level * 100:.2f}%"
        recommendation = prediction.get_recommendation()
        reasoning = prediction.explain_reasoning()
        
        # Parse details
        if prediction.details and isinstance(prediction.details, str):
            details = json.loads(prediction.details)
        else:
            details = prediction.details or {}
        
        # Format details for display
        sbsk_compliance = details.get('sbsk_compliance', {})
        existing_assets = details.get('existing_assets', {})
        asset_condition = details.get('asset_condition', {})
        
        result_data = [
            ["Status Prediksi", result_text],
            ["Tingkat Keyakinan", confidence],
            ["Tanggal Prediksi", prediction.created_at.strftime("%d %B %Y %H:%M")]
        ]
        
        # Create table for prediction result
        result_table = Table(result_data, colWidths=[4 * cm, 12 * cm])
        result_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.green if prediction.prediction_result else colors.red)
        ]))
        
        content.append(result_table)
        content.append(Spacer(1, 0.5 * cm))
        
        # Add analysis details
        content.append(Paragraph("DETAIL ANALISIS", subtitle_style))
        
        # SBSK compliance
        sbsk_text = sbsk_compliance.get('description', 'Tidak ada informasi kepatuhan SBSK.')
        content.append(Paragraph("<b>Kesesuaian dengan SBSK:</b>", normal_style))
        content.append(Paragraph(sbsk_text, normal_style))
        content.append(Spacer(1, 0.3 * cm))
        
        # Existing assets
        existing_text = existing_assets.get('description', 'Tidak ada informasi aset eksisting.')
        content.append(Paragraph("<b>Optimalisasi Aset yang Ada:</b>", normal_style))
        content.append(Paragraph(existing_text, normal_style))
        content.append(Spacer(1, 0.3 * cm))
        
        # Asset condition
        condition_text = asset_condition.get('description', 'Tidak ada informasi kondisi aset.')
        content.append(Paragraph("<b>Kondisi Aset:</b>", normal_style))
        content.append(Paragraph(condition_text, normal_style))
        content.append(Spacer(1, 0.5 * cm))
        
        # Add recommendation
        content.append(Paragraph("REKOMENDASI", subtitle_style))
        content.append(Paragraph(recommendation, normal_style))
        content.append(Spacer(1, 0.5 * cm))
        
        # Add footer
        footer_text = f"Dokumen ini dibuat secara otomatis oleh sistem Assets Planning Prediction (APP) pada {datetime.now().strftime('%d %B %Y %H:%M')}"
        content.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey
        )))
        
        # Build the PDF
        doc.build(content)
        
        # Set buffer position to the beginning
        buffer.seek(0)
        
        # Create file name
        filename = f"Prediksi_RKBMN_{asset_request.request_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        # Send the PDF as attachment
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Terjadi kesalahan saat mengekspor PDF: {str(e)}', 'danger')
        return redirect(url_for('prediction.result', prediction_id=prediction.id))