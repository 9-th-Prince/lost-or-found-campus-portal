import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'campus-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'lost_or_found.db')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('study_group.id'), primary_key=True)
)

# --- DATABASE MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    items = db.relationship('Item', backref='author', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_type = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.String(120), nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='Open')
    security_question = db.Column(db.String(200), nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    claims = db.relationship('Claim', backref='item', cascade='all, delete-orphan', lazy=True)

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    claimant_name = db.Column(db.String(100), nullable=False)
    claimant_contact = db.Column(db.String(120), nullable=False)
    answer = db.Column(db.String(300), nullable=False)
    is_seen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class StudyGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('User', secondary=group_members, backref='study_groups')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_type = db.Column(db.String(20), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- GLOBAL NAVBAR NOTIFICATION BADGES ---
@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        unread_msgs = ChatMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        unseen_claims = Claim.query.join(Item).filter(Item.user_id == current_user.id, Claim.is_seen == False).count()
        return dict(unread_msgs=unread_msgs, unseen_claims=unseen_claims)
    return dict(unread_msgs=0, unseen_claims=0)

# --- LIVE AUTO-CHECK APIS ---
@app.route('/api/notifications')
@login_required
def api_notifications():
    unread_msgs = ChatMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    unseen_claims = Claim.query.join(Item).filter(Item.user_id == current_user.id, Claim.is_seen == False).count()
    return jsonify({'unread_msgs': unread_msgs, 'unseen_claims': unseen_claims})

@app.route('/api/chat_messages')
@login_required
def api_chat_messages():
    room_type = request.args.get('room_type', 'public')
    other_user_id = request.args.get('other_user_id', type=int)
    group_id = request.args.get('group_id', type=int)
    item_id = request.args.get('item_id', type=int)

    messages = []
    if room_type == 'public':
        messages = ChatMessage.query.filter_by(room_type='public').order_by(ChatMessage.timestamp.asc()).limit(100).all()
    elif room_type == 'private' and other_user_id:
        messages = ChatMessage.query.filter(
            ChatMessage.room_type == 'private',
            ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == other_user_id)) |
            ((ChatMessage.sender_id == other_user_id) & (ChatMessage.receiver_id == current_user.id))
        ).order_by(ChatMessage.timestamp.asc()).all()
        for m in messages:
            if m.receiver_id == current_user.id and not m.is_read:
                m.is_read = True
        db.session.commit()
    elif room_type == 'group' and group_id:
        group = StudyGroup.query.get(group_id)
        if group and current_user in group.members:
            messages = ChatMessage.query.filter_by(room_type='group', group_id=group_id).order_by(ChatMessage.timestamp.asc()).all()
    elif room_type == 'item' and item_id and other_user_id:
        messages = ChatMessage.query.filter(
            ChatMessage.room_type == 'item',
            ChatMessage.item_id == item_id,
            ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == other_user_id)) |
            ((ChatMessage.sender_id == other_user_id) & (ChatMessage.receiver_id == current_user.id))
        ).order_by(ChatMessage.timestamp.asc()).all()
        for m in messages:
            if m.receiver_id == current_user.id and not m.is_read:
                m.is_read = True
        db.session.commit()

    return jsonify([
        {
            'id': m.id,
            'is_me': m.sender_id == current_user.id,
            'sender_name': 'You' if m.sender_id == current_user.id else m.sender.name,
            'body': m.body,
            'time': m.timestamp.strftime('%I:%M %p')
        }
        for m in messages
    ])

# --- MAIN ROUTES ---

@app.route('/')
def index():
    search = request.args.get('search', '').strip()
    post_type = request.args.get('type', '')
    category = request.args.get('category', '')

    query = Item.query.order_by(Item.date_posted.desc())
    if search:
        query = query.filter(Item.title.ilike(f'%{search}%') | Item.location.ilike(f'%{search}%'))
    if post_type:
        query = query.filter_by(post_type=post_type)
    if category:
        query = query.filter_by(category=category)

    return render_template('index.html', items=query.all())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_name = request.form.get('name', '').strip()
        new_email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('new_password', '').strip()

        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != current_user.id:
            flash('That email is already used by another account.', 'danger')
            return redirect(url_for('profile'))

        current_user.name = new_name
        current_user.email = new_email
        if new_password:
            current_user.password = generate_password_hash(new_password)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    total_posts = Item.query.filter_by(user_id=current_user.id).count()
    resolved_posts = Item.query.filter_by(user_id=current_user.id, status='Resolved').count()
    total_claims = Claim.query.filter_by(user_id=current_user.id).count()

    return render_template(
        'profile.html',
        total_posts=total_posts,
        resolved_posts=resolved_posts,
        total_claims=total_claims
    )

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post_item():
    if request.method == 'POST':
        file = request.files.get('image')
        filename = None
        if file and file.filename:
            filename = f"{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        item = Item(
            post_type=request.form['post_type'],
            title=request.form['title'],
            category=request.form['category'],
            location=request.form['location'],
            description=request.form['description'],
            contact_info=request.form['contact_info'],
            security_question=request.form.get('security_question', '').strip(),
            image_filename=filename,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        flash('Your item has been posted!', 'success')
        return redirect(url_for('index'))
    return render_template('post_item.html')

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own posts.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        item.post_type = request.form['post_type']
        item.title = request.form['title']
        item.category = request.form['category']
        item.location = request.form['location']
        item.description = request.form['description']
        item.contact_info = request.form['contact_info']
        item.security_question = request.form.get('security_question', '').strip()

        file = request.files.get('image')
        if file and file.filename:
            filename = f"{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            item.image_filename = filename

        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_item.html', item=item)

@app.route('/item/<int:item_id>', methods=['GET', 'POST'])
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please log in to submit a claim so the poster can reply to you.', 'warning')
            return redirect(url_for('login'))

        claim = Claim(
            claimant_name=current_user.name,
            claimant_contact=request.form['claimant_contact'],
            answer=request.form['answer'],
            item_id=item.id,
            user_id=current_user.id
        )
        db.session.add(claim)
        db.session.commit()
        flash('Claim submitted! You can now chat on your Dashboard.', 'success')
        return redirect(url_for('item_detail', item_id=item.id))
    return render_template('item_detail.html', item=item)

@app.route('/dashboard')
@login_required
def dashboard():
    my_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.date_posted.desc()).all()
    my_claims = Claim.query.filter_by(user_id=current_user.id).all()

    for it in my_items:
        for cl in it.claims:
            if not cl.is_seen:
                cl.is_seen = True
    db.session.commit()

    smart_matches = []
    for it in my_items:
        if it.status == 'Open':
            opposite_type = 'Found' if it.post_type == 'Lost' else 'Lost'
            matches = Item.query.filter(
                Item.post_type == opposite_type,
                Item.category == it.category,
                Item.status == 'Open',
                Item.user_id != current_user.id
            ).all()
            for m in matches:
                smart_matches.append({'my_item': it, 'match': m})

    return render_template('dashboard.html', items=my_items, my_claims=my_claims, smart_matches=smart_matches)

@app.route('/item_chat/<int:item_id>/<int:other_user_id>', methods=['GET', 'POST'])
@login_required
def item_chat(item_id, other_user_id):
    item = Item.query.get_or_404(item_id)
    other_user = User.query.get_or_404(other_user_id)

    if request.method == 'POST':
        body = request.form.get('body', '').strip()
        if body:
            msg = ChatMessage(
                room_type='item',
                body=body,
                sender_id=current_user.id,
                receiver_id=other_user.id,
                item_id=item.id
            )
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('item_chat', item_id=item.id, other_user_id=other_user.id))

    thread = ChatMessage.query.filter(
        ChatMessage.room_type == 'item',
        ChatMessage.item_id == item.id,
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == other_user.id)) |
        ((ChatMessage.sender_id == other_user.id) & (ChatMessage.receiver_id == current_user.id))
    ).order_by(ChatMessage.timestamp.asc()).all()

    for m in thread:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()

    return render_template('item_chat.html', item=item, other_user=other_user, thread=thread)

# --- WHATSAPP-STYLE CAMPUS CHAT HUB ---

@app.route('/messages', methods=['GET', 'POST'])
@login_required
def inbox():
    tab = request.args.get('tab', 'public')
    user_search = request.args.get('q', '').strip()
    active_user_id = request.args.get('user_id', type=int)
    active_group_id = request.args.get('group_id', type=int)

    if request.method == 'POST':
        body = request.form.get('body', '').strip()
        msg_type = request.form.get('room_type')
        if body:
            if msg_type == 'public':
                db.session.add(ChatMessage(room_type='public', body=body, sender_id=current_user.id))
                db.session.commit()
                return redirect(url_for('inbox', tab='public'))
            elif msg_type == 'private' and active_user_id:
                db.session.add(ChatMessage(room_type='private', body=body, sender_id=current_user.id, receiver_id=active_user_id))
                db.session.commit()
                return redirect(url_for('inbox', tab='private', user_id=active_user_id))
            elif msg_type == 'group' and active_group_id:
                db.session.add(ChatMessage(room_type='group', body=body, sender_id=current_user.id, group_id=active_group_id))
                db.session.commit()
                return redirect(url_for('inbox', tab='groups', group_id=active_group_id))

    public_messages = ChatMessage.query.filter_by(room_type='public').order_by(ChatMessage.timestamp.asc()).limit(100).all()

    users_query = User.query.filter(User.id != current_user.id)
    if user_search:
        users_query = users_query.filter(User.name.ilike(f'%{user_search}%') | User.email.ilike(f'%{user_search}%'))
    searched_users = users_query.all()

    active_user = User.query.get(active_user_id) if active_user_id else None
    private_messages = []
    if active_user:
        private_messages = ChatMessage.query.filter(
            ChatMessage.room_type == 'private',
            ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == active_user.id)) |
            ((ChatMessage.sender_id == active_user.id) & (ChatMessage.receiver_id == current_user.id))
        ).order_by(ChatMessage.timestamp.asc()).all()

        unread_from_active = ChatMessage.query.filter_by(
            sender_id=active_user.id,
            receiver_id=current_user.id,
            is_read=False
        ).all()
        for m in unread_from_active:
            m.is_read = True
        db.session.commit()

    unread_rows = ChatMessage.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).all()
    unread_by_sender = {}
    for m in unread_rows:
        unread_by_sender[m.sender_id] = unread_by_sender.get(m.sender_id, 0) + 1

    all_groups = StudyGroup.query.order_by(StudyGroup.created_at.desc()).all()
    active_group = StudyGroup.query.get(active_group_id) if active_group_id else None
    group_messages = []
    if active_group:
        group_messages = ChatMessage.query.filter_by(room_type='group', group_id=active_group.id).order_by(ChatMessage.timestamp.asc()).all()

    return render_template(
        'inbox.html',
        tab=tab,
        user_search=user_search,
        public_messages=public_messages,
        searched_users=searched_users,
        active_user=active_user,
        private_messages=private_messages,
        unread_by_sender=unread_by_sender,
        all_groups=all_groups,
        active_group=active_group,
        group_messages=group_messages
    )

@app.route('/create_group', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if name:
        group = StudyGroup(name=name, description=description)
        group.members.append(current_user)
        db.session.add(group)
        db.session.commit()
        flash(f'Study Group "{name}" created!', 'success')
        return redirect(url_for('inbox', tab='groups', group_id=group.id))
    return redirect(url_for('inbox', tab='groups'))

@app.route('/join_group/<int:group_id>')
@login_required
def join_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    if current_user not in group.members:
        group.members.append(current_user)
        db.session.commit()
        flash(f'Joined "{group.name}"!', 'success')
    return redirect(url_for('inbox', tab='groups', group_id=group.id))

@app.route('/leave_group/<int:group_id>')
@login_required
def leave_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    if current_user in group.members:
        group.members.remove(current_user)
        db.session.commit()
        flash(f'You left "{group.name}".', 'info')
    return redirect(url_for('inbox', tab='groups'))

@app.route('/resolve/<int:item_id>')
@login_required
def resolve_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id == current_user.id or current_user.is_admin:
        item.status = 'Resolved' if item.status == 'Open' else 'Open'
        db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id == current_user.id or current_user.is_admin:
        db.session.delete(item)
        db.session.commit()
        flash('Post deleted.', 'info')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Admin access required.', 'danger')
        return redirect(url_for('index'))
    return render_template('admin.html', items=Item.query.order_by(Item.date_posted.desc()).all(), users=User.query.all())

# --- INITIALIZE DB & DEFAULT ADMIN ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@campus.edu').first():
        admin = User(
            name='Campus Admin',
            email='admin@campus.edu',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)