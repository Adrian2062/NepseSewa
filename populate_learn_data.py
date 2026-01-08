import os
import django

import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

try:
    from myapp.models import Course, Lesson, CandlestickPattern, Quiz, Question, QuizOption
except Exception:
    with open('populate_error.txt', 'w') as f:
        f.write("Import Error:\n")
        f.write(traceback.format_exc())
    sys.exit(1)

def populate():
    try:
        print("Creating Courses...")
    
    # 1. Stock Market Basics
    c1, created = Course.objects.get_or_create(
        title="Stock Market Basics",
        defaults={
            'description': "Learn how the NEPSE works, what are shares, and how to start investing safely.",
            'difficulty': 'Beginner',
            'is_active': True
        }
    )
    
    if created:
        Lesson.objects.create(course=c1, title="What is NEPSE?", content="<p>NEPSE stands for Nepal Stock Exchange...</p>", order=1, duration_minutes=5)
        Lesson.objects.create(course=c1, title="How to Open a DEMAT Account?", content="<p>To trade in Nepal, you need a Demat account...</p>", order=2, duration_minutes=10)
        Lesson.objects.create(course=c1, title="Understanding IPOs", content="<p>IPO (Initial Public Offering) is...</p>", order=3, duration_minutes=7)
        print(f"Created Course: {c1.title}")
    else:
        print(f"Course {c1.title} already exists.")

    # 2. Technical Analysis
    c2, created = Course.objects.get_or_create(
        title="Technical Analysis Masterclass",
        defaults={
            'description': "Master charts, patterns, and indicators to predict price movements.",
            'difficulty': 'Intermediate',
            'is_active': True
        }
    )
    
    if created:
        Lesson.objects.create(course=c2, title="Introduction to Candlesticks", content="<p>Candlesticks represent price movement...</p>", order=1, duration_minutes=15)
        Lesson.objects.create(course=c2, title="Support and Resistance", content="<p>Support is a level where price tends to bounce up...</p>", order=2, duration_minutes=20)
        print(f"Created Course: {c2.title}")

    # 3. AI Price Prediction (Educational)
    c3, created = Course.objects.get_or_create(
        title="AI in Stock Trading",
        defaults={
            'description': "Understand how our LSTM model predicts stock prices and what metrics like RMSE mean.",
            'difficulty': 'Advanced',
            'is_active': True
        }
    )
    
    if created:
        Lesson.objects.create(course=c3, title="What is LSTM?", content="<p>LSTM (Long Short-Term Memory) is a type of Recurrent Neural Network...</p>", order=1, duration_minutes=10)
        Lesson.objects.create(course=c3, title="Understanding RMSE & MAE", content="<p>RMSE (Root Mean Square Error) measures the accuracy...</p>", order=2, duration_minutes=12)
        print(f"Created Course: {c3.title}")

    # Patterns
    print("Creating Candlestick Patterns...")
    patterns = [
        ("Hammer", "Bullish", "A bullish reversal pattern that forms after a decline."),
        ("Shooting Star", "Bearish", "A bearish reversal pattern that forms after an advance."),
        ("Doji", "Neutral", "Indicates indecision in the market."),
    ]
    
    for name, p_type, desc in patterns:
        p, created = CandlestickPattern.objects.get_or_create(name=name, defaults={'pattern_type': p_type, 'description': desc})
        if created:
            print(f"Created Pattern: {name}")

    # Quiz
    print("Creating Daily Quiz...")
    q, created = Quiz.objects.get_or_create(title="Market Indicators Quiz")
    if created:
        ques1 = Question.objects.create(quiz=q, text="Which indicator is used to measure volatility?", order=1)
        QuizOption.objects.create(question=ques1, text="Bollinger Bands", is_correct=True)
        QuizOption.objects.create(question=ques1, text="RSI", is_correct=False)
        QuizOption.objects.create(question=ques1, text="Moving Average", is_correct=False)
        print("Created Quiz")

    print("Done!")

    except Exception:
        with open('populate_error.txt', 'w') as f:
            f.write("Runtime Error:\n")
            f.write(traceback.format_exc())
        print("Error logged to populate_error.txt")

if __name__ == '__main__':
    populate()
