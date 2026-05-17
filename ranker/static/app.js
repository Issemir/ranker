/**
 * Ranker Web App - JavaScript Client
 */

class Ranker {
    constructor() {
        this.state = "start";
        this.currentRound = 0;
        this.currentMatch = 0;
        this.totalRounds = 0;
        this.totalMatches = 0;
        this.totalMatchesInRound = 0;
        
        this.initializeEventListeners();
        this.checkAuth();
    }

    async checkAuth() {
        try {
            const response = await fetch("/api/user");
            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }
        } catch (error) {
            console.error("Auth check error:", error);
        }
    }

    initializeEventListeners() {
        // Start button
        document.getElementById("start-btn").addEventListener("click", () => this.startRanking());

        // Voting buttons
        document.getElementById("option1-btn").addEventListener("click", () => this.vote(1));
        document.getElementById("option2-btn").addEventListener("click", () => this.vote(2));

        // Results buttons
        document.getElementById("save-btn").addEventListener("click", () => this.saveRanking());
        document.getElementById("export-btn").addEventListener("click", () => this.exportResults());
        document.getElementById("restart-btn").addEventListener("click", () => this.restartRanking());

        // Logout button
        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => this.logout());
        }

        // Keyboard shortcuts
        document.addEventListener("keydown", (e) => {
            if (e.key === "1" || e.key === "2") {
                this.vote(parseInt(e.key));
            }
        });
    }

    async logout() {
        try {
            const response = await fetch("/api/logout", { method: "POST" });
            if (response.ok) {
                window.location.href = "/login";
            }
        } catch (error) {
            console.error("Logout error:", error);
            alert("Error logging out");
        }
    }

    async startRanking() {
        try {
            const response = await fetch("/api/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            
            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || "Error starting ranking. Please upload a file first.");
                return;
            }

            this.totalRounds = data.total_rounds;
            this.totalMatches = 0;
            this.currentRound = 0;
            this.currentMatch = 0;

            this.showVotingScreen();
            await this.loadNextMatch();
        } catch (error) {
            console.error("Error starting ranking:", error);
            alert("Error starting ranking. Please upload a file first.");
        }
    }

    async loadNextMatch() {
        try {
            const response = await fetch("/api/next-match");
            const data = await response.json();

            if (data.status === "match") {
                this.currentRound = data.round;
                this.currentMatch = data.match;
                this.totalMatchesInRound = data.total_matches;

                document.getElementById("round-display").textContent = `Round ${data.round}`;
                document.getElementById("match-display").textContent = `Match ${data.match}/${data.total_matches}`;

                document.getElementById("option1-text").textContent = data.option1.name;
                document.getElementById("option2-text").textContent = data.option2.name;

                // Reset button states
                document.getElementById("option1-btn").classList.remove("selected");
                document.getElementById("option2-btn").classList.remove("selected");

                this.updateProgressBar();
            } else if (data.status === "complete") {
                await this.showResults();
            }
        } catch (error) {
            console.error("Error loading match:", error);
        }
    }

    async vote(choice) {
        if (this.state !== "voting") return;

        try {
            const response = await fetch("/api/vote", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ choice })
            });

            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }

            const data = await response.json();

            // Show selected button
            const btnClass = choice === 1 ? "option1-btn" : "option2-btn";
            document.getElementById(btnClass).classList.add("selected");

            // Wait a bit before loading next match
            await new Promise(resolve => setTimeout(resolve, 600));

            await this.loadNextMatch();
        } catch (error) {
            console.error("Error recording vote:", error);
        }
    }

    async showResults() {
        try {
            const response = await fetch("/api/results");
            const data = await response.json();

            if (data.status === "complete") {
                this.displayResults(data.rankings);
                this.showResultsScreen();
            }
        } catch (error) {
            console.error("Error fetching results:", error);
        }
    }

    displayResults(rankings) {
        const rankingsList = document.getElementById("rankings-list");
        rankingsList.innerHTML = "";

        rankings.forEach((item) => {
            const medal = item.rank === 1 ? "🥇" : item.rank === 2 ? "🥈" : item.rank === 3 ? "🥉" : "";
            
            const rankingItem = document.createElement("div");
            rankingItem.className = "ranking-item";
            rankingItem.innerHTML = `
                <div class="rank-badge">
                    ${medal || item.rank}
                </div>
                <div class="rank-info">
                    <div class="rank-name">${this.escapeHtml(item.name)}</div>
                    <div class="rank-stats">${item.wins}W - ${item.losses}L</div>
                </div>
                <div class="rank-score">
                    <div class="rank-score-percent">${item.score_percent}</div>
                    <div class="rank-score-record">Score: ${(item.score * 100).toFixed(1)}</div>
                </div>
            `;
            rankingsList.appendChild(rankingItem);
        });
    }

    async saveRanking() {
        const sessionName = document.getElementById("session-name").value || "Unnamed Ranking";

        try {
            const response = await fetch("/api/save-ranking", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_name: sessionName })
            });

            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }

            const data = await response.json();

            if (data.status === "saved") {
                alert("✓ Ranking saved to history!");
                document.getElementById("save-btn").textContent = "Saved!";
                document.getElementById("save-btn").disabled = true;
            }
        } catch (error) {
            console.error("Error saving ranking:", error);
            alert("Error saving ranking");
        }
    }

    async exportResults() {
        try {
            const response = await fetch("/api/export", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ path: "rankings.txt" })
            });

            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }

            const data = await response.json();

            if (data.status === "exported") {
                alert(`Results exported to ${data.path}`);
            }
        } catch (error) {
            console.error("Error exporting results:", error);
            alert("Error exporting results");
        }
    }

    restartRanking() {
        location.reload();
    }

    updateProgressBar() {
        const totalVotes = this.totalRounds * this.totalMatchesInRound;
        const currentVotes = (this.currentRound - 1) * this.totalMatchesInRound + (this.currentMatch - 1);
        const percentage = totalVotes > 0 ? (currentVotes / totalVotes) * 100 : 0;

        document.querySelector(".progress-fill").style.width = `${percentage}%`;
    }

    showVotingScreen() {
        this.state = "voting";
        this.showScreen("voting-screen");
    }

    showResultsScreen() {
        this.state = "results";
        this.showScreen("results-screen");
    }

    showScreen(screenId) {
        document.querySelectorAll(".screen").forEach(screen => {
            screen.classList.remove("active");
        });
        document.getElementById(screenId).classList.add("active");
    }

    escapeHtml(text) {
        const map = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    window.ranker = new Ranker();
});
