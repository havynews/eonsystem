from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import News, USER_PRODUCTS

news_bp = Blueprint("news", __name__)


@news_bp.route('/news')
def list():
    news = News.query.order_by(News.published_at.desc()).all()
    return render_template('news/news_list.html', news=news)

@news_bp.route('/news/<int:news_id>')
def detail(news_id):
    news = News.query.get_or_404(news_id)
    return render_template('news/detail.html', news=news)