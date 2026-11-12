document.addEventListener("DOMContentLoaded", function () {
    const filterButtons = document.querySelectorAll(".order-filter");
    const orderCards = document.querySelectorAll("[data-order-status]");
    const emptyMessage = document.getElementById("empty-filter-message");
    const messagesButton = document.querySelectorAll(".toggle-messages-btn");
    const messageForm = document.querySelectorAll(".send-message-form");

    filterButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const selectedStatus = this.dataset.filter;

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

            let visibleCount = 0;

            orderCards.forEach(function (card) {
                const orderStatus = card.dataset.orderStatus;

                const matches =
                    selectedStatus === "all" ||
                    orderStatus === selectedStatus;

                card.hidden = !matches;

                if(matches){
                    visibleCount++;
                }
            });
            emptyMessage.hidden = visibleCount > 0;
        });
    });
    

    messagesButton.forEach(function(button){
         button.addEventListener("click",function(){
        const buttonId = button.dataset.orderId;
        const messagesList = document.getElementById(`messages-list-${buttonId}`);
        const panel = document.getElementById(`messages-panel-${buttonId}`);
                         
            if(!panel){
             return;
            }

            panel.hidden = !panel.hidden;

            button.textContent = panel.hidden ? "مشاهده پیام ها" : "بستن پیام ها";

            button.setAttribute("aria-expanded",String(!panel.hidden));

            const url = messagesList.dataset.messagesUrl;
            fetch(url).then(response=>{
                if(!response.ok){
                    throw new Error(`HTTP Error :${response.status}`);
                }
                return response.json();
            }).then(data=>{
                messagesList.innerHTML = "";
                data.messages.forEach(function(message){
                    const messageElement = document.createElement("div");
                    messageElement.textContent = message.message;
                    messagesList.appendChild(messageElement);
                });
            }).catch(error => {
                console.error("error :",error);
         });
        });
    });
    messageForm.forEach(function(form){
        form.addEventListener("submit",function(event){
            const csrfToken = form.querySelector("input[name='csrfmiddlewaretoken']").value;
            event.preventDefault();

            const orderId = form.dataset.orderId;
            const inputMessage = document.getElementById(`message-input-${orderId}`);
            const messagesList = document.getElementById(`messages-list-${orderId}`);

            if (!inputMessage){
                return;
            }

            const messageText = inputMessage.value.trim();
            if(messageText == ""){
                alert("لطفا متن پیام را وارد کنید");
                return;
            }
            const url = form.dataset.sendUrl;
            console.log(url);
            console.log("CSRF Token:", csrfToken);
            fetch(url,{
                method:"POST",
                headers: {
                  "Content-Type": "application/json",
                  "X-CSRFToken": csrfToken
                 },
                body:JSON.stringify({
                    "message":messageText
                })
            }).then(async response=>{
                data = await response.json();
                if (!response.ok){
                    throw new Error(data.error || `HTTP Error : ${response.status}`);
                }
                return data;
            }).then(data=>{
                const messageElement = document.createElement("div");
                messageElement.textContent = data.message;
                messagesList.appendChild(messageElement);
                inputMessage.value = "";
            }).catch(error=>{
                console.error("خطا در ارسال پیام:",error);
                alert(error.message);
            });
        });         
    });
});
