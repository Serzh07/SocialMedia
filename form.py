from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

class MessageForm(FlaskForm):
    content = StringField("Message", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Send")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class AddPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    text = StringField("Text", validators=[DataRequired()])
    submit = SubmitField('Post')