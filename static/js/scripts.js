function changeMember(select) {
    const memberId = select.value;
    window.location.href = `{{ url_for('meal_planner') }}?member_id=${memberId}`;
}