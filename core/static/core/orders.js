document.addEventListener("DOMContentLoaded", function () {
    const filterButtons = document.querySelectorAll(".order-filter");
    const orderCards = document.querySelectorAll("[data-order-status]");

    console.log("Filter buttons:", filterButtons.length);
    console.log("Order cards:", orderCards.length);

    filterButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const selectedStatus = this.dataset.filter;

            console.log("Selected filter:", selectedStatus);

            filterButtons.forEach(function (item) {
                item.classList.remove("bg-indigo-600", "text-white");
                item.classList.add(
                    "border",
                    "border-slate-200",
                    "bg-white",
                    "text-slate-600"
                );
            });

            this.classList.remove(
                "border",
                "border-slate-200",
                "bg-white",
                "text-slate-600"
            );

            this.classList.add("bg-indigo-600", "text-white");

            orderCards.forEach(function (card) {
                const orderStatus = card.dataset.orderStatus;

                const matches =
                    selectedStatus === "all" ||
                    orderStatus === selectedStatus;

                card.hidden = !matches;

                console.log({
                    orderStatus: orderStatus,
                    selectedStatus: selectedStatus,
                    matches: matches
                });
            });
        });
    });
});
