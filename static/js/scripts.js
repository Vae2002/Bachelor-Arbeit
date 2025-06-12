function changeMember(select) {
    const memberId = select.value;

    // Save to localStorage
    localStorage.setItem("selectedMemberId", memberId);

    // Redirect to same path with new member_id
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set("member_id", memberId);
    window.location.href = currentUrl.toString();
}