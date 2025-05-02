from app import db
from app.models.prediction import Prediction
from app.models.sbsk_validator import SBSKValidator
import json

class PredictionService:
    """Service for generating predictions"""
    
    def generate_prediction(self, asset_request):
        """
        Generate a prediction for an asset request
        
        Args:
            asset_request: The AssetRequest object
            
        Returns:
            Prediction object with the result
        """
        # Create a new prediction
        prediction = Prediction(request_id=asset_request.id)
        db.session.add(prediction)
        db.session.commit()
        
        try:
            # Get validator for the asset code
            validator = SBSKValidator(asset_request.asset_code)
            
            # Validate request against SBSK
            result = validator.validate_sbsk(asset_request)
            
            # Update prediction with results
            prediction.prediction_result = result['approved']
            prediction.confidence_level = result['confidence']
            
            # Convert details to JSON if needed
            if isinstance(result['details'], dict):
                prediction.details = json.dumps(result['details'])
            else:
                prediction.details = result['details']
            
            db.session.commit()
            
            return prediction
            
        except Exception as e:
            # Log error
            import traceback
            print(f"Error generating prediction: {str(e)}")
            print(traceback.format_exc())
            
            # Set error details
            prediction.prediction_result = False
            prediction.confidence_level = 0.5
            prediction.details = json.dumps({
                'error': True,
                'message': str(e),
                'sbsk_compliance': {
                    'met': False,
                    'description': f"Terjadi kesalahan saat memvalidasi: {str(e)}"
                },
                'existing_assets': {
                    'optimized': False,
                    'description': "Tidak dapat memeriksa optimalisasi aset karena terjadi kesalahan."
                },
                'asset_condition': {
                    'description': "Tidak dapat memeriksa kondisi aset karena terjadi kesalahan."
                }
            })
            
            db.session.commit()
            
            return prediction
    
    def get_prediction_stats(self, satker_id=None):
        """
        Get prediction statistics
        
        Args:
            satker_id: Optional satker ID to filter stats
            
        Returns:
            Dictionary with prediction statistics
        """
        from app.models.asset_request import AssetRequest
        from sqlalchemy import func
        
        # Base query
        query = db.session.query(
            func.count(Prediction.id).label('total'),
            func.sum(Prediction.prediction_result.cast(db.Integer)).label('approved'),
            func.sum((~Prediction.prediction_result).cast(db.Integer)).label('rejected')
        )
        
        # Apply satker filter if provided
        if satker_id:
            query = query.join(AssetRequest).filter(AssetRequest.satker_id == satker_id)
        
        # Execute query
        result = query.first()
        
        # Calculate percentages
        total = result.total or 0
        approved = result.approved or 0
        rejected = result.rejected or 0
        
        approved_percent = (approved / total) * 100 if total > 0 else 0
        rejected_percent = (rejected / total) * 100 if total > 0 else 0
        
        return {
            'total': total,
            'approved': approved,
            'approved_percent': approved_percent,
            'rejected': rejected,
            'rejected_percent': rejected_percent
        }
    
    def get_predictions_by_month(self, start_date, end_date, satker_id=None):
        """
        Get prediction counts by month
        
        Args:
            start_date: Start date
            end_date: End date
            satker_id: Optional satker ID to filter stats
            
        Returns:
            List of dictionaries with monthly prediction counts
        """
        from app.models.asset_request import AssetRequest
        from sqlalchemy import func, extract
        from datetime import datetime
        
        # Base query
        query = db.session.query(
            extract('year', Prediction.created_at).label('year'),
            extract('month', Prediction.created_at).label('month'),
            func.count(Prediction.id).label('total'),
            func.sum(Prediction.prediction_result.cast(db.Integer)).label('approved'),
            func.sum((~Prediction.prediction_result).cast(db.Integer)).label('rejected')
        ).group_by(
            extract('year', Prediction.created_at),
            extract('month', Prediction.created_at)
        ).filter(
            Prediction.created_at.between(start_date, end_date)
        )
        
        # Apply satker filter if provided
        if satker_id:
            query = query.join(AssetRequest).filter(AssetRequest.satker_id == satker_id)
        
        # Execute query
        results = query.all()
        
        # Format results
        monthly_data = []
        for row in results:
            month_date = datetime(int(row.year), int(row.month), 1)
            monthly_data.append({
                'month': month_date.strftime('%b %Y'),
                'total': row.total or 0,
                'approved': row.approved or 0,
                'rejected': row.rejected or 0
            })
        
        return monthly_data
    
    def get_approval_rate_by_asset_code(self, satker_id=None, limit=10):
        """
        Get approval rate by asset code
        
        Args:
            satker_id: Optional satker ID to filter stats
            limit: Maximum number of asset codes to return
            
        Returns:
            List of dictionaries with asset code approval rates
        """
        from app.models.asset_request import AssetRequest
        from sqlalchemy import func
        
        # Base query
        query = db.session.query(
            AssetRequest.asset_code,
            AssetRequest.asset_name,
            func.count(Prediction.id).label('total'),
            func.sum(Prediction.prediction_result.cast(db.Integer)).label('approved'),
            func.sum((~Prediction.prediction_result).cast(db.Integer)).label('rejected')
        ).join(
            AssetRequest, Prediction.request_id == AssetRequest.id
        ).group_by(
            AssetRequest.asset_code, AssetRequest.asset_name
        ).order_by(
            func.count(Prediction.id).desc()
        ).limit(limit)
        
        # Apply satker filter if provided
        if satker_id:
            query = query.filter(AssetRequest.satker_id == satker_id)
        
        # Execute query
        results = query.all()
        
        # Format results
        asset_code_data = []
        for row in results:
            total = row.total or 0
            approved = row.approved or 0
            approval_rate = (approved / total) * 100 if total > 0 else 0
            
            asset_code_data.append({
                'asset_code': row.asset_code,
                'asset_name': row.asset_name,
                'total': total,
                'approved': approved,
                'approval_rate': approval_rate
            })
        
        return asset_code_data