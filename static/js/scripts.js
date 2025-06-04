function changeMember(select) {
    const memberId = select.value;
    const currentPath = window.location.pathname;
    const selectedWeek = document.getElementById("selected_week_header")?.value;

    if (currentPath.includes("/meal_planner")) {
        let url = `/meal_planner?member_id=${memberId}`;
        if (selectedWeek) {
            url += `&week=${selectedWeek}`;
        }
        console.log("Redirecting to:", url);
        window.location.href = url;
    } else if (currentPath.includes("/recipe_lookup")) {
        let url = `/recipe_lookup?member_id=${memberId}`;
        console.log("Redirecting to:", url);
        window.location.href = url;
    } else {
        let fallbackUrl = `/meal_planner?member_id=${memberId}`;
        console.log("Redirecting to fallback:", fallbackUrl);
        window.location.href = fallbackUrl;
    }
}
