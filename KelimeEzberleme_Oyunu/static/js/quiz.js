function updateTimer() {
    const totalSeconds = parseInt(document.getElementById('timer-data').dataset.seconds);
    
    function update() {
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        
        document.getElementById('hours').textContent = hours.toString().padStart(2, '0');
        document.getElementById('minutes').textContent = minutes.toString().padStart(2, '0');
        document.getElementById('seconds').textContent = seconds.toString().padStart(2, '0');
        
        if (totalSeconds > 0) {
            totalSeconds--;
            setTimeout(update, 1000);
        } else {
            window.location.reload();
        }
    }
    
    update();
}

document.addEventListener('DOMContentLoaded', function() {
    const quizForm = document.getElementById('quizForm');
    if (quizForm) {
        quizForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Bekleyin...';
            
            setTimeout(() => {
                this.submit();
            }, 2000);
        });
    }

    if (document.getElementById('timer-data')) {
        updateTimer();
    }
}); 