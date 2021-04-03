from http import HTTPStatus
import json
import yaml
from flask import request, render_template, jsonify, redirect, abort
from flask_smorest import Blueprint
from flask_login import login_required
from app.models import Host, Group


views = Blueprint('views', __name__)


@views.route('/upload', methods=['GET'])
@login_required
def get_upload_file():
    return render_template('upload.html')