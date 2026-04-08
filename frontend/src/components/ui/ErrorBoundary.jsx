import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error(`[ErrorBoundary${this.props.name ? `: ${this.props.name}` : ''}]`, error, errorInfo);
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }
            return (
                <div className="error-boundary-fallback">
                    <AlertTriangle size={24} />
                    <p>{this.props.name ? `${this.props.name} encountered an error` : 'Something went wrong'}</p>
                    <button onClick={this.handleReset}>
                        <RefreshCw size={14} />
                        Try again
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}
