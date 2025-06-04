function changeMember(select) {
    const memberId = select.value;
    localStorage.setItem("selectedMemberId", memberId); // Store selection

    const currentPath = window.location.pathname;
    const selectedWeek = document.getElementById("selected_week_header")?.value;

    let url;
    if (currentPath.includes("/profile")) {
        url = `/profile?member_id=${memberId}`;
    } else if (currentPath.includes("/recipe_lookup")) {
        url = `/recipe_lookup?member_id=${memberId}`;
    } else if (currentPath.includes("/meal_planner")) {
        url = `/meal_planner?member_id=${memberId}`;
        if (selectedWeek) {
            url += `&week=${selectedWeek}`;
        }
    } else {
        // Default/fallback
        url = `/meal_planner?member_id=${memberId}`;
    }

    console.log("Redirecting to:", url);
    window.location.href = url;
}
