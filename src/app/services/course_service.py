from datetime import datetime, timezone
from src.app.models.course_model import (
    CourseModel, ModuleModel, LessonModel, ActivityModel,
    QuestionModel, StudentAnswerModel, LessonViewModel,
)


class CourseService:

    # ── Courses ───────────────────────────────────────────────────────────────

    @staticmethod
    def create_course(name, description, classroom_id, teacher_id):
        course = CourseModel(
            name=name,
            description=description,
            classroom_id=classroom_id,
            teacher_id=teacher_id,
        )
        return course.save_to_db()

    @staticmethod
    def get_courses_by_classroom(classroom_id):
        courses = CourseModel.get_by_classroom(classroom_id)
        for course in courses:
            course['has_content'] = CourseModel.has_visible_content(course['_id'])
        return {'courses': courses}

    @staticmethod
    def get_courses_for_user(user_id):
        from src.app.services.classroom_service import ClassroomService

        classrooms_result = ClassroomService.getClassrooms(user_id)
        classrooms = classrooms_result.get('classrooms') or []
        courses = []
        for classroom in classrooms:
            if classroom.get('user_role') != 'student':
                continue
            classroom_id = classroom.get('_id')
            classroom_name = classroom.get('name') or ''
            classroom_courses = CourseModel.get_by_classroom(classroom_id)
            for course in classroom_courses:
                if not CourseModel.has_visible_content(course['_id']):
                    continue
                course['classroom_id'] = classroom_id
                course['classroom_name'] = classroom_name
                course['has_content'] = True
                courses.append(course)
        return {'courses': courses}

    @staticmethod
    def get_course_detail(course_id, user_id=None, is_teacher=False):
        course = CourseModel.get_by_id(course_id)
        if not course:
            return None
        if user_id is not None:
            is_teacher = str(course.get('teacher_id')) == str(user_id)
        # Teachers of this course see all modules; students only see released ones
        modules = ModuleModel.get_by_course(course_id, include_hidden=is_teacher)
        for module in modules:
            # Once a module is visible, content follows its own individual settings.
            # Teachers always see everything inside.
            module['lessons'] = LessonModel.get_by_module(
                module['_id'], include_hidden=is_teacher
            )
            module['activities'] = ActivityModel.get_by_module(
                module['_id'], include_hidden=is_teacher
            )
        course['modules'] = modules
        return course

    @staticmethod
    def update_course(course_id, update_data):
        CourseModel.update(course_id, update_data)
        return CourseModel.get_by_id(course_id)

    @staticmethod
    def delete_course(course_id):
        modules = ModuleModel.get_by_course(course_id)
        for module in modules:
            CourseService.delete_module(module['_id'])
        CourseModel.delete(course_id)
        return {}

    # ── Modules ───────────────────────────────────────────────────────────────

    @staticmethod
    def create_module(name, course_id, scheduled_at=None):
        module = ModuleModel(name=name, course_id=course_id, scheduled_at=scheduled_at)
        return module.save_to_db()

    @staticmethod
    def update_module(module_id, update_data):
        if 'scheduled_at' in update_data:
            if update_data['scheduled_at']:
                try:
                    update_data['scheduled_at'] = datetime.fromisoformat(
                        update_data['scheduled_at']
                    )
                except (ValueError, TypeError):
                    update_data.pop('scheduled_at', None)
            else:
                update_data['scheduled_at'] = None
        ModuleModel.update(module_id, update_data)
        return ModuleModel.get_by_id(module_id)

    @staticmethod
    def delete_module(module_id):
        lessons = LessonModel.get_by_module(module_id)
        for lesson in lessons:
            LessonModel.delete(lesson['_id'])

        activities = ActivityModel.get_by_module(module_id)
        for activity in activities:
            QuestionModel.delete_by_activity(activity['_id'])
            StudentAnswerModel.delete_by_activity(activity['_id'])
            ActivityModel.delete(activity['_id'])

        ModuleModel.delete(module_id)
        return {}

    @staticmethod
    def reorder_modules(course_id, module_ids):
        ModuleModel.reorder(course_id, module_ids)
        return {}

    # ── Lessons ───────────────────────────────────────────────────────────────

    @staticmethod
    def create_lesson(title, video_url, video_type, description,
                      module_id, course_id, visible, scheduled_at):
        lesson = LessonModel(
            title=title,
            video_url=video_url,
            video_type=video_type,
            description=description,
            module_id=module_id,
            course_id=course_id,
            visible=visible,
            scheduled_at=scheduled_at,
        )
        return lesson.save_to_db()

    @staticmethod
    def update_lesson(lesson_id, update_data):
        if update_data.get('scheduled_at'):
            try:
                update_data['scheduled_at'] = datetime.fromisoformat(
                    update_data['scheduled_at']
                )
            except (ValueError, TypeError):
                update_data.pop('scheduled_at', None)
        LessonModel.update(lesson_id, update_data)
        return LessonModel.get_by_id(lesson_id)

    @staticmethod
    def delete_lesson(lesson_id):
        LessonModel.delete(lesson_id)
        return {}

    @staticmethod
    def reorder_lessons(module_id, lesson_ids):
        LessonModel.reorder(module_id, lesson_ids)
        return {}

    # ── Activities ────────────────────────────────────────────────────────────

    @staticmethod
    def create_activity(title, description, module_id, course_id, visible, scheduled_at):
        activity = ActivityModel(
            title=title,
            description=description,
            module_id=module_id,
            course_id=course_id,
            visible=visible,
            scheduled_at=scheduled_at,
        )
        return activity.save_to_db()

    @staticmethod
    def get_activity_detail(activity_id, is_teacher=False):
        activity = ActivityModel.get_by_id(activity_id)
        if not activity:
            return None
        activity['questions'] = QuestionModel.get_by_activity(
            activity_id, for_student=not is_teacher
        )
        return activity

    @staticmethod
    def update_activity(activity_id, update_data):
        if update_data.get('scheduled_at'):
            try:
                update_data['scheduled_at'] = datetime.fromisoformat(
                    update_data['scheduled_at']
                )
            except (ValueError, TypeError):
                update_data.pop('scheduled_at', None)
        ActivityModel.update(activity_id, update_data)
        return ActivityModel.get_by_id(activity_id)

    @staticmethod
    def delete_activity(activity_id):
        QuestionModel.delete_by_activity(activity_id)
        StudentAnswerModel.delete_by_activity(activity_id)
        ActivityModel.delete(activity_id)
        return {}

    @staticmethod
    def reorder_activities(module_id, activity_ids):
        ActivityModel.reorder(module_id, activity_ids)
        return {}

    # ── Questions ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_question(text, q_type, options, correct_answer,
                        show_answer, points, activity_id):
        question = QuestionModel(
            text=text,
            type=q_type,
            options=options,
            correct_answer=correct_answer,
            show_answer=show_answer,
            points=points,
            activity_id=activity_id,
        )
        return question.save_to_db()

    @staticmethod
    def update_question(question_id, update_data):
        QuestionModel.update(question_id, update_data)
        return QuestionModel.get_by_id(question_id)

    @staticmethod
    def delete_question(question_id):
        QuestionModel.delete(question_id)
        return {}

    # ── Lesson Views ─────────────────────────────────────────────────────────

    @staticmethod
    def mark_lesson_viewed(lesson_id, student_id):
        LessonViewModel.mark_viewed(lesson_id, student_id)
        return {}

    @staticmethod
    def get_lesson_view_status(lesson_id, student_id):
        viewed = LessonViewModel.has_viewed(lesson_id, student_id)
        return {'viewed': viewed}

    @staticmethod
    def get_students_progress(course_id):
        """Teacher-facing: returns enriched views + answers for every lesson/activity."""
        from src.app import mongo
        from bson import ObjectId as ObjId

        # ── Resolve classroom students ──────────────────────────────────────
        course = CourseModel.get_by_id(course_id)
        classroom_id = course.get('classroom_id') if course else None

        students_map = {}  # student_id -> {name, email}
        all_student_ids = []
        if classroom_id:
            classroom = mongo.db.classrooms.find_one({'_id': ObjId(classroom_id)})
            if classroom:
                raw_ids = classroom.get('students', [])
                all_student_ids = [str(sid) for sid in raw_ids]
                # Look up user documents for names/emails
                user_docs = list(mongo.db.users.find(
                    {'_id': {'$in': [ObjId(sid) for sid in all_student_ids]}},
                    {'_id': 1, 'name': 1, 'email': 1}
                ))
                for u in user_docs:
                    uid = str(u['_id'])
                    students_map[uid] = {
                        '_id': uid,
                        'name': u.get('name') or u.get('email', uid[-6:]),
                        'email': u.get('email', ''),
                    }

        def student_info(sid):
            return students_map.get(sid, {'_id': sid, 'name': sid[-6:], 'email': ''})

        # ── Build per-module data ───────────────────────────────────────────
        modules = ModuleModel.get_by_course(course_id)
        result = []

        for module in modules:
            mid = module['_id']
            lessons = LessonModel.get_by_module(mid, include_hidden=True)
            activities = ActivityModel.get_by_module(mid, include_hidden=True)

            lessons_data = []
            for lesson in lessons:
                raw_viewers = LessonViewModel.get_viewers(lesson['_id'])
                viewer_ids = {v['student_id'] for v in raw_viewers}
                viewers_enriched = [
                    {**v, **student_info(v['student_id'])}
                    for v in raw_viewers
                ]
                not_viewed = [
                    student_info(sid)
                    for sid in all_student_ids
                    if sid not in viewer_ids
                ]
                lessons_data.append({
                    '_id': lesson['_id'],
                    'title': lesson['title'],
                    'view_count': len(raw_viewers),
                    'viewers': viewers_enriched,
                    'not_viewed': not_viewed,
                })

            activities_data = []
            for activity in activities:
                raw_answers = StudentAnswerModel.get_by_activity(activity['_id'])
                submitted_ids = {a['student_id'] for a in raw_answers}
                submissions_enriched = [
                    {**a, **student_info(a['student_id'])}
                    for a in raw_answers
                ]
                not_submitted = [
                    student_info(sid)
                    for sid in all_student_ids
                    if sid not in submitted_ids
                ]
                scores = [
                    a['score'] for a in raw_answers
                    if a.get('score') is not None
                ]
                avg_score = (sum(scores) / len(scores)) if scores else None
                activities_data.append({
                    '_id': activity['_id'],
                    'title': activity['title'],
                    'submission_count': len(raw_answers),
                    'submissions': submissions_enriched,
                    'not_submitted': not_submitted,
                    'avg_score': round(avg_score, 1) if avg_score is not None else None,
                })

            result.append({
                'module_id': mid,
                'module_name': module['name'],
                'lessons': lessons_data,
                'activities': activities_data,
            })

        # ── "By student" pre-computed summary ──────────────────────────────
        student_summaries = {}
        for sid in all_student_ids:
            student_summaries[sid] = {
                **student_info(sid),
                'lessons_viewed': 0,
                'total_lessons': 0,
                'activities_submitted': 0,
                'total_activities': 0,
                'scores': [],
                'detail': [],          # list of {type, title, viewed/submitted/score}
            }

        for module in result:
            for lesson in module['lessons']:
                viewer_ids = {v['student_id'] for v in lesson['viewers']}
                for sid in all_student_ids:
                    if sid in student_summaries:
                        student_summaries[sid]['total_lessons'] += 1
                        viewed = sid in viewer_ids
                        if viewed:
                            student_summaries[sid]['lessons_viewed'] += 1
                        student_summaries[sid]['detail'].append({
                            'type': 'lesson',
                            'title': lesson['title'],
                            'module': module['module_name'],
                            'viewed': viewed,
                        })

            for activity in module['activities']:
                submitted_ids = {s['student_id'] for s in activity['submissions']}
                sub_by_student = {s['student_id']: s for s in activity['submissions']}
                for sid in all_student_ids:
                    if sid in student_summaries:
                        student_summaries[sid]['total_activities'] += 1
                        submitted = sid in submitted_ids
                        if submitted:
                            student_summaries[sid]['activities_submitted'] += 1
                            score = sub_by_student[sid].get('score')
                            if score is not None:
                                student_summaries[sid]['scores'].append(score)
                        student_summaries[sid]['detail'].append({
                            'type': 'activity',
                            'title': activity['title'],
                            'module': module['module_name'],
                            'submitted': submitted,
                            'score': sub_by_student[sid].get('score') if submitted else None,
                        })

        students_list = []
        for sid, summary in student_summaries.items():
            scores = summary.pop('scores')
            summary['avg_score'] = (
                round(sum(scores) / len(scores), 1) if scores else None
            )
            students_list.append(summary)

        return {
            'progress': result,
            'students': students_list,
            'total_students': len(all_student_ids),
        }

    # ── Teacher answer management ─────────────────────────────────────────────

    @staticmethod
    def get_student_answer_for_teacher(activity_id, student_id):
        """Return the student's submission alongside the activity questions."""
        from src.app.models.course_model import ActivityModel, QuestionModel
        activity = ActivityModel.get_by_id(activity_id)
        questions = QuestionModel.get_by_activity(activity_id)
        answer_doc = StudentAnswerModel.get_by_student_and_activity(student_id, activity_id)
        return {
            'activity': activity,
            'questions': questions,
            'answer': answer_doc,
        }

    @staticmethod
    def set_student_approved(activity_id, student_id, approved: bool):
        StudentAnswerModel.set_approved(activity_id, student_id, approved)
        return {'approved': approved}

    @staticmethod
    def reset_student_answer(activity_id, student_id):
        StudentAnswerModel.reset_by_student(activity_id, student_id)
        return {}

    # ── Student Answers ───────────────────────────────────────────────────────

    @staticmethod
    def submit_answers(student_id, activity_id, answers):
        questions = QuestionModel.get_by_activity(activity_id, for_student=False)
        question_map = {q['_id']: q for q in questions}

        total_points = sum(q.get('points', 1) for q in questions)
        earned_points = 0

        for answer in answers:
            q_id = str(answer.get('question_id', ''))
            student_ans = answer.get('answer')
            question = question_map.get(q_id)
            if not question:
                continue

            q_type = question.get('type')
            correct = question.get('correct_answer')

            if q_type in ('multiple_choice', 'dropdown', 'short_answer', 'fill_in_blank'):
                if correct is not None and (
                    str(student_ans).strip().lower() == str(correct).strip().lower()
                ):
                    earned_points += question.get('points', 1)
            elif q_type == 'checkbox':
                if isinstance(correct, list) and isinstance(student_ans, list):
                    if set(str(x) for x in student_ans) == set(str(x) for x in correct):
                        earned_points += question.get('points', 1)

        score = round((earned_points / total_points) * 100, 1) if total_points > 0 else None

        sa = StudentAnswerModel(
            student_id=student_id,
            activity_id=activity_id,
            answers=answers,
            score=score,
        )
        sa.save_to_db()
        return {
            'score': score,
            'earned_points': earned_points,
            'total_points': total_points,
        }

    @staticmethod
    def get_my_answer(student_id, activity_id):
        return StudentAnswerModel.get_by_student_and_activity(student_id, activity_id)
