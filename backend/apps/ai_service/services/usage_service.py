def _log_usage(self, user, endpoint, usage, response_time,
                   success=True, error_message=""):

        AIUsageLog.objects.create(
            user=user,
            endpoint=endpoint,
            model_used=self.model,
            response_time_ms=response_time,
            success=success,
            error_message=error_message
        )
