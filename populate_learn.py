
import os
import django
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "NepseSewa.settings")
django.setup()

from myapp.models import CourseCategory, Course, CandlestickLesson
from django.utils.text import slugify

def populate():
    print("Populating Learn data...")
    
    # 1. Categories
    categories = ['Technical Analysis', 'Fundamental Analysis', 'Trading Psychology']
    cat_objs = {}
    for name in categories:
        cat, created = CourseCategory.objects.get_or_create(
            name=name, 
            defaults={'slug': slugify(name)}
        )
        cat_objs[name] = cat
        print(f"Category: {name}")

    # 2. Courses
    courses_data = [
        {
            'title': 'Candlestick Mastery',
            'category': 'Technical Analysis',
            'difficulty': 'Beginner',
            'desc': 'Master the art of reading candlestick patterns to predict market movements.',
            'featured': True
        },
        {
            'title': 'RSI & Indicators',
            'category': 'Technical Analysis',
            'difficulty': 'Intermediate',
            'desc': 'Deep dive into RSI, MACD, and Bollinger Bands.',
            'featured': False
        },
        {
            'title': 'Value Investing 101',
            'category': 'Fundamental Analysis',
            'difficulty': 'Beginner',
            'desc': 'Learn how to read balance sheets and find undervalued stocks.',
            'featured': True
        }
    ]

    for c_data in courses_data:
        course, created = Course.objects.get_or_create(
            title=c_data['title'],
            defaults={
                'slug': slugify(c_data['title']),
                'category': cat_objs[c_data['category']],
                'description': c_data['desc'],
                'difficulty': c_data['difficulty'],
                'is_featured': c_data['featured']
            }
        )
        print(f"Course: {course.title}")
        
        # 3. Lessons
        if created:
            for i in range(1, 4):
                CandlestickLesson.objects.create(
                    course=course,
                    title=f"Lesson {i}: {course.title} Basics",
                    description=f"This is the content for lesson {i}. It covers key concepts...",
                    order=i
                )
            print(f" - Added 3 lessons to {course.title}")

if __name__ == "__main__":
    populate()
    print("Done! You can now run the server.")
